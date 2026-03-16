"""
Thread-safe async utilities for Extended SDK.

Ensures all async operations use the correct event loop when called
from ThreadPoolExecutor contexts in Celery workers.
"""

import asyncio
import threading
from typing import Any, Awaitable, List, Optional, Set, Tuple, TypeVar

import nest_asyncio

T = TypeVar("T")

# Thread-local storage for event loops
_thread_local = threading.local()


def get_current_loop() -> asyncio.AbstractEventLoop:
    """
    Get the current thread's event loop, creating one if needed.

    Thread-safe version that works with run_sync() from v1.0.1.
    Ensures each thread has its own event loop to prevent
    "Future attached to different loop" errors.

    Returns:
        The current thread's event loop
    """
    # Try to get running loop first
    try:
        return asyncio.get_running_loop()
    except RuntimeError:
        pass

    # Check thread-local storage
    loop = getattr(_thread_local, "loop", None)
    if loop is not None and not loop.is_closed():
        return loop

    # Check if we're in main thread
    is_main_thread = threading.current_thread() is threading.main_thread()

    if not is_main_thread:
        # Worker thread: create thread-local loop
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

    return loop


async def thread_safe_gather(
    *awaitables: Awaitable[Any],
    return_exceptions: bool = False,
) -> List[Any]:
    """
    Thread-safe version of asyncio.gather().

    Ensures all tasks are created in the current thread's event loop
    to prevent "Future attached to different loop" errors.

    Args:
        *awaitables: Coroutines or awaitables to run concurrently
        return_exceptions: If True, exceptions are returned as results
                          instead of being raised

    Returns:
        List of results from all awaitables
    """
    if not awaitables:
        return []

    # Get the current running loop (we're in async context)
    current_loop = asyncio.get_running_loop()

    # Process each awaitable to ensure they're compatible with current loop
    compatible_tasks = []
    for awaitable in awaitables:
        if asyncio.iscoroutine(awaitable):
            # Create task in current loop
            task = current_loop.create_task(awaitable)
            compatible_tasks.append(task)
        elif hasattr(awaitable, '_loop') and awaitable._loop != current_loop:
            # Task/Future from different loop - we need to recreate
            # This is the critical fix for the "different loop" error
            if hasattr(awaitable, '_coro') and awaitable._coro is not None:
                # It's a Task with coroutine, recreate in current loop
                task = current_loop.create_task(awaitable._coro)
                compatible_tasks.append(task)
            else:
                # It's a Future or completed Task - try to await it directly
                # This will raise the "different loop" error, so we catch and handle
                try:
                    # If it's already done, get the result
                    if awaitable.done():
                        if return_exceptions:
                            try:
                                result = awaitable.result()
                                compatible_tasks.append(asyncio.create_task(_return_result(result)))
                            except Exception as e:
                                compatible_tasks.append(asyncio.create_task(_return_result(e)))
                        else:
                            result = awaitable.result()
                            compatible_tasks.append(asyncio.create_task(_return_result(result)))
                    else:
                        # Not done and no coroutine - can't safely transfer
                        if return_exceptions:
                            error = RuntimeError(f"Cannot transfer pending future from different loop: {awaitable}")
                            compatible_tasks.append(asyncio.create_task(_return_result(error)))
                        else:
                            raise RuntimeError(f"Cannot transfer pending future from different loop: {awaitable}")
                except Exception as e:
                    if return_exceptions:
                        compatible_tasks.append(asyncio.create_task(_return_result(e)))
                    else:
                        raise
        else:
            # Same loop or no loop attribute, use as-is
            compatible_tasks.append(awaitable)

    return await asyncio.gather(*compatible_tasks, return_exceptions=return_exceptions)


async def _return_result(result: Any) -> Any:
    """Helper coroutine to return a value asynchronously."""
    return result


async def thread_safe_wait_for(
    awaitable: Awaitable[T],
    timeout: Optional[float] = None,
) -> T:
    """
    Thread-safe version of asyncio.wait_for().

    Args:
        awaitable: Coroutine or awaitable to run
        timeout: Maximum time to wait (None for no timeout)

    Returns:
        Result of the awaitable

    Raises:
        asyncio.TimeoutError: If timeout is exceeded
    """
    current_loop = asyncio.get_running_loop()

    if asyncio.iscoroutine(awaitable):
        task = current_loop.create_task(awaitable)
    else:
        task = awaitable

    return await asyncio.wait_for(task, timeout=timeout)


def thread_safe_create_task(
    coro: Awaitable[T],
    *,
    name: Optional[str] = None,
) -> asyncio.Task[T]:
    """
    Thread-safe version of asyncio.create_task().

    Creates a task in the current thread's event loop.

    Args:
        coro: Coroutine to wrap in a task
        name: Optional name for the task

    Returns:
        The created task
    """
    current_loop = get_current_loop()

    if name is not None:
        return current_loop.create_task(coro, name=name)
    else:
        return current_loop.create_task(coro)


async def thread_safe_wait(
    fs: Set[Awaitable[Any]],
    *,
    timeout: Optional[float] = None,
    return_when: str = asyncio.ALL_COMPLETED,
) -> Tuple[Set[asyncio.Task[Any]], Set[asyncio.Task[Any]]]:
    """
    Thread-safe version of asyncio.wait().

    Args:
        fs: Set of futures/coroutines to wait for
        timeout: Maximum time to wait
        return_when: When to return (ALL_COMPLETED, FIRST_COMPLETED, FIRST_EXCEPTION)

    Returns:
        Tuple of (done, pending) task sets
    """
    current_loop = asyncio.get_running_loop()

    # Ensure all futures are tasks in current loop
    tasks = set()
    for f in fs:
        if asyncio.iscoroutine(f):
            task = current_loop.create_task(f)
        else:
            task = f
        tasks.add(task)

    return await asyncio.wait(tasks, timeout=timeout, return_when=return_when)
