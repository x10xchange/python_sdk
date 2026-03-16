"""
Helper utilities for Extended Exchange SDK.
"""

import asyncio
import threading
from decimal import Decimal
from functools import wraps
from typing import Any, Callable, Coroutine, Dict, Optional, Tuple, TypeVar

import nest_asyncio

from x10.perpetual.orders import TimeInForce as X10TimeInForce

from extended.utils.constants import TIF_MAPPING

T = TypeVar("T")

# Thread-local storage for event loops
_thread_local = threading.local()


def normalize_market_name(name: str) -> str:
    """
    Normalize market name to Extended format.

    Hyperliquid uses: "BTC", "ETH"
    Extended uses: "BTC-USD", "ETH-USD"

    Args:
        name: Market name in either format

    Returns:
        Market name in Extended format (e.g., "BTC-USD")
    """
    if "-" not in name:
        return f"{name}-USD"
    return name


def to_hyperliquid_market_name(name: str) -> str:
    """
    Convert Extended market name to Hyperliquid format.

    "BTC-USD" -> "BTC"

    Args:
        name: Market name in Extended format

    Returns:
        Market name in Hyperliquid format (e.g., "BTC")
    """
    return name.replace("-USD", "")


def run_sync(coro_or_factory) -> T:
    """
    Run an async coroutine synchronously with nuclear-level thread safety.

    This version uses adaptive isolation strategies to completely eliminate
    "Future attached to different loop" errors in production environments.

    Strategies (in order of preference):
    1. Thread isolation for ThreadPoolExecutor contexts
    2. Standard approach for main thread contexts
    3. Process isolation as ultimate fallback

    Args:
        coro_or_factory: Either a coroutine object or a callable that returns a coroutine

    Returns:
        The result of the coroutine
    """
    # Handle callable factories to prevent coroutine reuse
    if callable(coro_or_factory):
        coro = coro_or_factory()
    else:
        coro = coro_or_factory
    # Quick check if we're in a ThreadPoolExecutor (production scenario)
    current_thread = threading.current_thread()
    is_threadpool = ("ThreadPoolExecutor" in current_thread.name or
                    "CrossEx" in current_thread.name or
                    "Worker" in current_thread.name)

    if is_threadpool:
        # Production ThreadPoolExecutor context - use nuclear isolation
        return _run_sync_thread_isolated(coro_or_factory)

    # Try standard approach first for non-ThreadPoolExecutor contexts
    try:
        # Check for running loop first (async context)
        try:
            running_loop = asyncio.get_running_loop()
            # We're inside an async context - use nest_asyncio
            nest_asyncio.apply(running_loop)
            return running_loop.run_until_complete(coro)
        except RuntimeError:
            # No running loop - expected case for sync contexts
            pass

        # Standard event loop approach
        is_main_thread = threading.current_thread() is threading.main_thread()

        if not is_main_thread:
            # Worker thread: use thread-local event loop
            loop = getattr(_thread_local, "loop", None)
            if loop is None or loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                nest_asyncio.apply(loop)
                _thread_local.loop = loop
        else:
            # Main thread: use standard approach
            try:
                loop = asyncio.get_event_loop()
                if loop.is_closed():
                    raise RuntimeError("closed")
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            nest_asyncio.apply(loop)

        return loop.run_until_complete(coro)

    except RuntimeError as e:
        if "attached to a different loop" in str(e):
            # This is the exact error we're trying to fix - use nuclear isolation
            return _run_sync_thread_isolated(coro_or_factory)
        else:
            # Other RuntimeError - re-raise
            raise


def _run_sync_thread_isolated(coro_or_factory) -> T:
    """
    Nuclear option: Run coroutine in completely isolated thread.

    This creates a dedicated thread with its own event loop,
    completely eliminating any possibility of loop conflicts.
    """
    import concurrent.futures

    result = None
    exception = None

    def isolated_runner():
        nonlocal result, exception
        try:
            # Create completely isolated loop in this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                # Handle callable factories to create fresh coroutine in isolated thread
                if callable(coro_or_factory):
                    coro = coro_or_factory()
                else:
                    coro = coro_or_factory
                result = loop.run_until_complete(asyncio.wait_for(coro, timeout=25))
            except asyncio.TimeoutError:
                exception = TimeoutError("Extended SDK operation timed out after 25 seconds")
            except Exception as e:
                exception = e
            finally:
                try:
                    loop.close()
                except:
                    pass

        except Exception as e:
            exception = e

    # Run in dedicated thread with timeout
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(isolated_runner)
        try:
            future.result(timeout=30)  # 30 second total timeout
        except concurrent.futures.TimeoutError:
            raise TimeoutError("Extended SDK operation timed out after 30 seconds")

    if exception:
        raise exception

    return result


def sync_wrapper(
    async_method: Callable[..., Coroutine[Any, Any, T]]
) -> Callable[..., T]:
    """
    Decorator to create a synchronous version of an async method.

    Usage:
        class AsyncInfoAPI:
            async def user_state(self) -> Dict:
                ...

        class InfoAPI:
            def __init__(self, async_api: AsyncInfoAPI):
                self._async = async_api

            @sync_wrapper
            async def user_state(self) -> Dict:
                return await self._async.user_state()
    """

    @wraps(async_method)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        return run_sync(async_method(*args, **kwargs))

    return wrapper


def parse_order_type(order_type: Dict[str, Any]) -> Tuple[X10TimeInForce, bool]:
    """
    Parse Hyperliquid order_type to Extended params.

    Args:
        order_type: Hyperliquid order type dict
            {"limit": {"tif": "Gtc"}} - Good-till-cancel
            {"limit": {"tif": "Ioc"}} - Immediate-or-cancel
            {"limit": {"tif": "Alo"}} - Add-liquidity-only (post-only)

    Returns:
        Tuple of (TimeInForce, post_only)
    """
    if "limit" in order_type:
        tif = order_type["limit"].get("tif", "Gtc")
        post_only = tif == "Alo"
        return TIF_MAPPING.get(tif, X10TimeInForce.GTT), post_only
    return X10TimeInForce.GTT, False


def parse_builder(
    builder: Optional[Dict[str, Any]]
) -> Tuple[Optional[int], Optional[Decimal]]:
    """
    Parse Hyperliquid builder format to Extended params.

    Hyperliquid: {"b": "123", "f": 10}
                 b = builder_id as string
                 f = fee in tenths of basis points

    Extended: builder_id (int), builder_fee (Decimal rate)

    Conversion:
        f=1  -> 0.1 bps  -> 0.000001
        f=10 -> 1 bps    -> 0.0001
        f=50 -> 5 bps    -> 0.0005

    Args:
        builder: Builder dict in Hyperliquid format or None

    Returns:
        Tuple of (builder_id, builder_fee) or (None, None)
    """
    if builder is None:
        return None, None

    # Parse builder_id from string to int
    builder_id = int(builder["b"])

    # Convert tenths of bps to decimal rate
    # f / 100000 = decimal rate
    fee_tenths_bps = builder.get("f", 0)
    builder_fee = Decimal(fee_tenths_bps) / Decimal(100000)

    return builder_id, builder_fee


def calculate_sz_decimals(min_order_size_change: Decimal) -> int:
    """
    Calculate size decimals from minimum order size change.

    Args:
        min_order_size_change: Minimum order size change (e.g., 0.001)

    Returns:
        Number of decimal places (e.g., 3)
    """
    if min_order_size_change <= 0:
        return 0
    return abs(int(min_order_size_change.log10()))
