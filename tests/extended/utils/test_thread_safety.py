"""
Comprehensive test suite for thread-safe async operations.

Tests the fixes for:
- RuntimeError: Task got Future attached to a different loop
- ThreadPoolExecutor contexts
- Celery worker contexts (simulated)
- Nested event loops
- Multiple concurrent threads
"""

import asyncio
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import AsyncMock, Mock, patch

import pytest

from extended.utils.async_helpers import (
    get_current_loop,
    thread_safe_create_task,
    thread_safe_gather,
    thread_safe_wait,
    thread_safe_wait_for,
)
from extended.utils.helpers import run_sync


class TestRunSync:
    """Tests for the thread-safe run_sync function."""

    def test_basic_sync_call(self):
        """Test basic synchronous execution of async coroutine."""

        async def simple_async():
            return "hello"

        result = run_sync(simple_async())
        assert result == "hello"

    def test_async_with_await(self):
        """Test async function with internal await."""

        async def async_with_sleep():
            await asyncio.sleep(0.01)
            return "slept"

        result = run_sync(async_with_sleep())
        assert result == "slept"

    def test_nested_run_sync(self):
        """Test nested run_sync calls (with nest_asyncio)."""

        async def inner():
            return "inner_result"

        async def outer():
            # This would fail without nest_asyncio
            return run_sync(inner())

        result = run_sync(outer())
        assert result == "inner_result"

    def test_deeply_nested_run_sync(self):
        """Test deeply nested run_sync calls."""

        async def level3():
            return "level3"

        async def level2():
            return run_sync(level3())

        async def level1():
            return run_sync(level2())

        result = run_sync(level1())
        assert result == "level3"

    def test_run_sync_preserves_exceptions(self):
        """Test that exceptions propagate correctly."""

        async def raising_async():
            raise ValueError("test error")

        with pytest.raises(ValueError, match="test error"):
            run_sync(raising_async())

    def test_run_sync_with_return_value_types(self):
        """Test various return value types."""

        async def return_dict():
            return {"key": "value"}

        async def return_list():
            return [1, 2, 3]

        async def return_none():
            return None

        assert run_sync(return_dict()) == {"key": "value"}
        assert run_sync(return_list()) == [1, 2, 3]
        assert run_sync(return_none()) is None


class TestRunSyncThreadPoolExecutor:
    """Tests for run_sync in ThreadPoolExecutor contexts."""

    def test_single_thread_executor(self):
        """Test run_sync in single-threaded executor."""

        def worker():
            async def async_work():
                await asyncio.sleep(0.01)
                return "worker_done"

            return run_sync(async_work())

        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(worker)
            result = future.result(timeout=5)

        assert result == "worker_done"

    def test_multi_thread_executor_parallel(self):
        """Test multiple parallel calls in ThreadPoolExecutor."""

        def worker(n):
            async def async_work():
                await asyncio.sleep(0.01)
                return f"worker_{n}"

            return run_sync(async_work())

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(worker, i) for i in range(5)]
            results = [f.result(timeout=10) for f in futures]

        assert len(results) == 5
        assert set(results) == {f"worker_{i}" for i in range(5)}

    def test_high_concurrency_executor(self):
        """Test with high concurrency to stress test loop isolation."""

        def worker(n):
            async def async_work():
                await asyncio.sleep(0.001)
                return n

            return run_sync(async_work())

        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(worker, i) for i in range(100)]
            results = [f.result(timeout=30) for f in futures]

        assert len(results) == 100
        assert set(results) == set(range(100))

    def test_executor_with_nested_run_sync(self):
        """Test nested run_sync inside ThreadPoolExecutor."""

        def worker(n):
            async def inner():
                await asyncio.sleep(0.01)
                return f"inner_{n}"

            async def outer():
                return run_sync(inner())

            return run_sync(outer())

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(worker, i) for i in range(5)]
            results = [f.result(timeout=10) for f in futures]

        assert results == [f"inner_{i}" for i in range(5)]

    def test_executor_exception_handling(self):
        """Test exception handling in ThreadPoolExecutor context."""

        def worker(should_fail):
            async def async_work():
                if should_fail:
                    raise ValueError("intentional failure")
                return "success"

            return run_sync(async_work())

        with ThreadPoolExecutor(max_workers=2) as executor:
            future_success = executor.submit(worker, False)
            future_failure = executor.submit(worker, True)

            assert future_success.result(timeout=5) == "success"

            with pytest.raises(ValueError, match="intentional failure"):
                future_failure.result(timeout=5)


class TestThreadSafeGather:
    """Tests for thread_safe_gather function."""

    @pytest.mark.asyncio
    async def test_basic_gather(self):
        """Test basic gather functionality."""

        async def task1():
            await asyncio.sleep(0.01)
            return "result1"

        async def task2():
            await asyncio.sleep(0.01)
            return "result2"

        results = await thread_safe_gather(task1(), task2())
        assert results == ["result1", "result2"]

    @pytest.mark.asyncio
    async def test_gather_empty(self):
        """Test gather with no arguments."""
        results = await thread_safe_gather()
        assert results == []

    @pytest.mark.asyncio
    async def test_gather_single_task(self):
        """Test gather with single task."""

        async def single():
            return "single"

        results = await thread_safe_gather(single())
        assert results == ["single"]

    @pytest.mark.asyncio
    async def test_gather_with_exceptions_returned(self):
        """Test gather with return_exceptions=True."""

        async def success():
            return "success"

        async def failure():
            raise ValueError("test error")

        results = await thread_safe_gather(
            success(), failure(), return_exceptions=True
        )

        assert results[0] == "success"
        assert isinstance(results[1], ValueError)
        assert str(results[1]) == "test error"

    @pytest.mark.asyncio
    async def test_gather_with_exceptions_raised(self):
        """Test gather with return_exceptions=False (default)."""

        async def success():
            return "success"

        async def failure():
            raise ValueError("test error")

        with pytest.raises(ValueError, match="test error"):
            await thread_safe_gather(success(), failure())

    @pytest.mark.asyncio
    async def test_gather_preserves_order(self):
        """Test that results are in the same order as inputs."""

        async def delayed(n, delay):
            await asyncio.sleep(delay)
            return n

        # Tasks with different delays
        results = await thread_safe_gather(
            delayed(1, 0.03),
            delayed(2, 0.01),
            delayed(3, 0.02),
        )

        # Results should be in input order, not completion order
        assert results == [1, 2, 3]

    def test_gather_in_threadpool_executor(self):
        """Test thread_safe_gather inside ThreadPoolExecutor."""

        def worker(n):
            async def async_work():
                async def task1():
                    await asyncio.sleep(0.01)
                    return f"task1_{n}"

                async def task2():
                    await asyncio.sleep(0.01)
                    return f"task2_{n}"

                return await thread_safe_gather(task1(), task2())

            return run_sync(async_work())

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(worker, i) for i in range(5)]
            results = [f.result(timeout=10) for f in futures]

        for i, result in enumerate(results):
            assert result == [f"task1_{i}", f"task2_{i}"]


class TestThreadSafeWaitFor:
    """Tests for thread_safe_wait_for function."""

    @pytest.mark.asyncio
    async def test_basic_wait_for(self):
        """Test basic wait_for functionality."""

        async def slow_task():
            await asyncio.sleep(0.01)
            return "done"

        result = await thread_safe_wait_for(slow_task(), timeout=5.0)
        assert result == "done"

    @pytest.mark.asyncio
    async def test_wait_for_timeout(self):
        """Test wait_for with timeout exceeded."""

        async def very_slow_task():
            await asyncio.sleep(10)
            return "done"

        with pytest.raises(asyncio.TimeoutError):
            await thread_safe_wait_for(very_slow_task(), timeout=0.01)

    @pytest.mark.asyncio
    async def test_wait_for_no_timeout(self):
        """Test wait_for without timeout."""

        async def task():
            await asyncio.sleep(0.01)
            return "no_timeout"

        result = await thread_safe_wait_for(task(), timeout=None)
        assert result == "no_timeout"


class TestThreadSafeCreateTask:
    """Tests for thread_safe_create_task function."""

    @pytest.mark.asyncio
    async def test_create_task_basic(self):
        """Test basic task creation."""

        async def task_coro():
            await asyncio.sleep(0.01)
            return "task_result"

        task = thread_safe_create_task(task_coro())
        result = await task
        assert result == "task_result"

    @pytest.mark.asyncio
    async def test_create_task_with_name(self):
        """Test task creation with name."""

        async def named_coro():
            return "named"

        task = thread_safe_create_task(named_coro(), name="my_task")
        assert task.get_name() == "my_task"
        result = await task
        assert result == "named"


class TestThreadSafeWait:
    """Tests for thread_safe_wait function."""

    @pytest.mark.asyncio
    async def test_wait_all_completed(self):
        """Test wait with ALL_COMPLETED."""

        async def task(n):
            await asyncio.sleep(0.01 * n)
            return n

        tasks = {task(1), task(2), task(3)}
        done, pending = await thread_safe_wait(tasks)

        assert len(done) == 3
        assert len(pending) == 0

    @pytest.mark.asyncio
    async def test_wait_first_completed(self):
        """Test wait with FIRST_COMPLETED."""

        async def fast_task():
            await asyncio.sleep(0.01)
            return "fast"

        async def slow_task():
            await asyncio.sleep(1)
            return "slow"

        tasks = {fast_task(), slow_task()}
        done, pending = await thread_safe_wait(
            tasks, return_when=asyncio.FIRST_COMPLETED
        )

        assert len(done) == 1
        assert len(pending) == 1

        # Cancel pending tasks
        for task in pending:
            task.cancel()


class TestGetCurrentLoop:
    """Tests for get_current_loop function."""

    def test_main_thread_loop(self):
        """Test getting loop in main thread."""
        loop = get_current_loop()
        assert loop is not None
        assert isinstance(loop, asyncio.AbstractEventLoop)
        assert not loop.is_closed()

    def test_worker_thread_loop_isolation(self):
        """Test that worker threads get isolated loops."""

        def get_loop_info():
            loop = get_current_loop()
            return {
                "loop_id": id(loop),
                "thread_id": threading.get_ident(),
                "is_closed": loop.is_closed(),
            }

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(get_loop_info) for _ in range(3)]
            results = [f.result() for f in futures]

        # All loops should be open
        for r in results:
            assert not r["is_closed"]

        # All threads should be different
        thread_ids = [r["thread_id"] for r in results]
        assert len(set(thread_ids)) == 3

        # All loops should be different
        loop_ids = [r["loop_id"] for r in results]
        assert len(set(loop_ids)) == 3

    def test_same_thread_same_loop(self):
        """Test that same thread gets same loop on repeated calls."""

        def get_loops():
            loop1 = get_current_loop()
            loop2 = get_current_loop()
            loop3 = get_current_loop()
            return [id(loop1), id(loop2), id(loop3)]

        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(get_loops)
            loop_ids = future.result()

        # All should be the same loop
        assert len(set(loop_ids)) == 1


class TestStrategySimulation:
    """
    Tests simulating the actual strategy execution pattern
    that was causing the original errors.
    """

    def test_cross_exchange_data_acquisition_pattern(self):
        """
        Simulate _acquire_cross_exchange_data from the trading strategy.

        This is the exact pattern that was failing with:
        RuntimeError: Task got Future attached to a different loop
        """

        def simulate_api_call(method_name, *args):
            """Simulate Extended SDK API calls."""

            async def async_api():
                # Simulate network delay
                await asyncio.sleep(0.01)

                if method_name == "user_state":
                    # Simulate user_state which uses asyncio.gather internally
                    async def get_balance():
                        await asyncio.sleep(0.005)
                        return {"balance": "1000"}

                    async def get_positions():
                        await asyncio.sleep(0.005)
                        return [{"symbol": "BTC", "size": "0.1"}]

                    balance, positions = await thread_safe_gather(
                        get_balance(), get_positions()
                    )
                    return {
                        "assetPositions": positions,
                        "marginSummary": {"accountValue": balance["balance"]},
                    }

                elif method_name == "meta":
                    return {"universe": [{"name": "BTC", "szDecimals": 5}]}

                elif method_name == "all_mids":
                    return {"BTC": "50000", "ETH": "3000"}

                else:
                    raise ValueError(f"Unknown method: {method_name}")

            return run_sync(async_api())

        # Simulate strategy's ThreadPoolExecutor pattern
        with ThreadPoolExecutor(max_workers=10, thread_name_prefix="CrossEx") as executor:
            futures = {}
            futures[executor.submit(simulate_api_call, "user_state")] = (
                "user_state",
                "client",
            )
            futures[executor.submit(simulate_api_call, "meta")] = ("meta", "client")
            futures[executor.submit(simulate_api_call, "all_mids")] = (
                "all_mids",
                "client",
            )

            results = {}
            failed_sources = []

            for future in as_completed(futures):
                key, source = futures[future]
                try:
                    timeout = 20 if key in ["user_state", "all_mids", "meta"] else 15
                    result = future.result(timeout=timeout)
                    results[key] = result
                except Exception as e:
                    failed_sources.append((key, str(e)))

        # Verify no failures
        assert len(failed_sources) == 0, f"Failed sources: {failed_sources}"

        # Verify all results
        assert "user_state" in results
        assert "meta" in results
        assert "all_mids" in results

        assert "assetPositions" in results["user_state"]
        assert "universe" in results["meta"]
        assert "BTC" in results["all_mids"]

    def test_multiple_strategy_iterations(self):
        """
        Test multiple iterations of the strategy pattern
        to ensure no accumulated state issues.
        """

        def single_iteration(iteration):
            def api_call(n):
                async def work():
                    await asyncio.sleep(0.01)
                    return f"iter_{iteration}_call_{n}"

                return run_sync(work())

            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = [executor.submit(api_call, i) for i in range(3)]
                return [f.result(timeout=5) for f in futures]

        # Run multiple iterations
        for i in range(10):
            results = single_iteration(i)
            assert len(results) == 3
            assert all(f"iter_{i}" in r for r in results)

    def test_mixed_sync_and_async_api_calls(self):
        """Test mixing sync and async API patterns."""

        def sync_api_call():
            return "sync_result"

        def async_api_call():
            async def work():
                await asyncio.sleep(0.01)
                return "async_result"

            return run_sync(work())

        def gather_api_call():
            async def work():
                async def t1():
                    return "gather_1"

                async def t2():
                    return "gather_2"

                return await thread_safe_gather(t1(), t2())

            return run_sync(work())

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(sync_api_call): "sync",
                executor.submit(async_api_call): "async",
                executor.submit(gather_api_call): "gather",
            }

            results = {}
            for future in as_completed(futures):
                key = futures[future]
                results[key] = future.result(timeout=5)

        assert results["sync"] == "sync_result"
        assert results["async"] == "async_result"
        assert results["gather"] == ["gather_1", "gather_2"]


class TestEdgeCases:
    """Tests for edge cases and potential issues."""

    def test_rapid_loop_creation(self):
        """Test rapid creation and use of loops in many threads."""

        def quick_work(n):
            async def work():
                return n

            return run_sync(work())

        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(quick_work, i) for i in range(200)]
            results = [f.result(timeout=30) for f in futures]

        assert len(results) == 200
        assert set(results) == set(range(200))

    def test_long_running_async_tasks(self):
        """Test with longer-running async tasks."""

        def long_worker(n):
            async def work():
                await asyncio.sleep(0.1)
                return n

            return run_sync(work())

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(long_worker, i) for i in range(5)]
            results = [f.result(timeout=10) for f in futures]

        assert len(results) == 5

    def test_exception_in_gather(self):
        """Test exception handling within gathered tasks in ThreadPool."""

        def worker():
            async def work():
                async def success():
                    return "ok"

                async def failure():
                    raise RuntimeError("task failed")

                return await thread_safe_gather(
                    success(), failure(), return_exceptions=True
                )

            return run_sync(work())

        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(worker)
            result = future.result(timeout=5)

        assert result[0] == "ok"
        assert isinstance(result[1], RuntimeError)

    def test_sequential_then_parallel(self):
        """Test sequential calls followed by parallel calls."""

        # Sequential calls first
        async def seq_task():
            return "seq"

        for _ in range(5):
            result = run_sync(seq_task())
            assert result == "seq"

        # Then parallel calls
        def parallel_worker(n):
            async def work():
                await asyncio.sleep(0.01)
                return f"parallel_{n}"

            return run_sync(work())

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(parallel_worker, i) for i in range(5)]
            results = [f.result(timeout=10) for f in futures]

        assert len(results) == 5

    def test_main_thread_interleaved_with_workers(self):
        """Test main thread calls interleaved with worker thread calls."""
        results = []

        # Main thread call
        async def main_task():
            return "main"

        results.append(("main_1", run_sync(main_task())))

        # Worker calls
        def worker(n):
            async def work():
                return f"worker_{n}"

            return run_sync(work())

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(worker, i) for i in range(2)]
            for i, f in enumerate(futures):
                results.append((f"worker_{i}", f.result(timeout=5)))

        # Main thread call again
        results.append(("main_2", run_sync(main_task())))

        assert len(results) == 4
        assert results[0] == ("main_1", "main")
        assert results[-1] == ("main_2", "main")


class TestMemoryAndPerformance:
    """Tests for memory usage and performance characteristics."""

    def test_no_loop_accumulation(self):
        """
        Test that we don't accumulate event loops.
        ThreadPoolExecutor reuses threads, so loops should be reused too.
        """

        def get_loop_id():
            loop = get_current_loop()
            return id(loop)

        with ThreadPoolExecutor(max_workers=2) as executor:
            # Submit many tasks (more than workers)
            futures = [executor.submit(get_loop_id) for _ in range(20)]
            loop_ids = [f.result() for f in futures]

        # Should only have 2 unique loops (one per worker)
        unique_loops = len(set(loop_ids))
        assert unique_loops <= 2, f"Expected max 2 loops, got {unique_loops}"

    def test_performance_not_degraded(self):
        """Test that thread-safe operations don't significantly degrade performance."""

        async def simple_task():
            return 1

        # Measure direct call time
        start = time.time()
        for _ in range(100):
            run_sync(simple_task())
        direct_time = time.time() - start

        # Measure ThreadPoolExecutor time
        def worker():
            return run_sync(simple_task())

        start = time.time()
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(worker) for _ in range(100)]
            [f.result() for f in futures]
        executor_time = time.time() - start

        # Executor should not be dramatically slower (allow 10x overhead for thread management)
        assert executor_time < direct_time * 10, (
            f"Performance degradation too high: {executor_time:.3f}s vs {direct_time:.3f}s"
        )
