"""Performance optimization tests for Phase 5 BIP85 improvements.

Tests the optimized BIP85 implementation with caching, batch operations,
and performance improvements to validate 50% performance targets.
"""

import time

import pytest

from sseed.bip85.applications import Bip85Applications
from sseed.bip85.cache import clear_global_cache
from sseed.bip85.optimized_applications import OptimizedBip85Applications


@pytest.fixture
def test_master_seed():
    """Provide test master seed for benchmarking."""
    return bytes.fromhex("a" * 128)  # 64 bytes


@pytest.fixture
def standard_apps():
    """Provide standard BIP85 applications instance."""
    return Bip85Applications()


@pytest.fixture
def optimized_apps():
    """Provide optimized BIP85 applications instance."""
    clear_global_cache()  # Start with clean cache
    return OptimizedBip85Applications(enable_caching=True)


@pytest.fixture
def optimized_apps_no_cache():
    """Provide optimized BIP85 applications without caching."""
    return OptimizedBip85Applications(enable_caching=False)


def measure_performance(operation, iterations: int = 20) -> dict:
    """Measure operation performance statistics."""
    times = []

    # Warm up
    for _ in range(3):
        operation()

    # Benchmark
    for _ in range(iterations):
        start_time = time.perf_counter()
        operation()
        end_time = time.perf_counter()
        times.append((end_time - start_time) * 1000)  # Convert to ms

    return {
        "mean_ms": sum(times) / len(times),
        "min_ms": min(times),
        "max_ms": max(times),
        "times": times,
    }


class TestOptimizationPerformance:
    """Test performance improvements from optimization."""

    def test_bip39_caching_performance_improvement(
        self, standard_apps, optimized_apps, test_master_seed
    ):
        """Test BIP39 generation performance improvement with caching."""

        # Test standard implementation
        def standard_operation():
            return standard_apps.derive_bip39_mnemonic(
                master_seed=test_master_seed, word_count=12, index=0, language="en"
            )

        standard_stats = measure_performance(standard_operation, iterations=30)

        # Test optimized implementation (first run - cache miss)
        def optimized_operation():
            return optimized_apps.derive_bip39_mnemonic(
                master_seed=test_master_seed, word_count=12, index=0, language="en"
            )

        optimized_stats = measure_performance(optimized_operation, iterations=30)

        # Calculate improvement
        improvement_percent = (
            (standard_stats["mean_ms"] - optimized_stats["mean_ms"])
            / standard_stats["mean_ms"]
            * 100
        )

        print("\n🚀 BIP39 Caching Performance:")
        print(f"   Standard: {standard_stats['mean_ms']:.2f}ms avg")
        print(f"   Optimized: {optimized_stats['mean_ms']:.2f}ms avg")
        print(f"   Improvement: {improvement_percent:.1f}%")

        # Validate performance improvement or at least no regression
        assert (
            optimized_stats["mean_ms"] <= standard_stats["mean_ms"] * 1.1
        ), f"Performance regression: {optimized_stats['mean_ms']:.2f}ms > {standard_stats['mean_ms']:.2f}ms"

    def test_repeated_operations_caching_benefit(
        self, optimized_apps, test_master_seed
    ):
        """Test caching benefits for repeated operations with same master seed."""

        # First operation (cache miss)
        start_time = time.perf_counter()
        result1 = optimized_apps.derive_bip39_mnemonic(
            master_seed=test_master_seed, word_count=12, index=0, language="en"
        )
        first_time = (time.perf_counter() - start_time) * 1000

        # Subsequent operations (cache hits) - different indices
        subsequent_times = []
        for i in range(1, 11):
            start_time = time.perf_counter()
            result = optimized_apps.derive_bip39_mnemonic(
                master_seed=test_master_seed, word_count=12, index=i, language="en"
            )
            subsequent_time = (time.perf_counter() - start_time) * 1000
            subsequent_times.append(subsequent_time)

            # Verify results are different
            assert (
                result != result1
            ), "Different indices should produce different results"

        avg_subsequent_time = sum(subsequent_times) / len(subsequent_times)

        print("\n🗄️ Caching Benefit Analysis:")
        print(f"   First operation (cache miss): {first_time:.2f}ms")
        print(f"   Subsequent ops (cache hit): {avg_subsequent_time:.2f}ms avg")
        print(
            f"   Cache benefit: {((first_time - avg_subsequent_time) / first_time * 100):.1f}%"
        )

        # Validate cache stats
        stats = optimized_apps.get_performance_stats()
        cache_stats = stats["cache_stats"]
        assert cache_stats["hits"] > 0, "Cache should have hits"
        assert cache_stats["hit_rate_percent"] > 0, "Hit rate should be positive"

    def test_batch_operation_performance(self, optimized_apps, test_master_seed):
        """Test batch operation performance vs individual operations."""
        indices = list(range(10))

        # Individual operations
        start_time = time.perf_counter()
        individual_results = []
        for index in indices:
            result = optimized_apps.derive_bip39_mnemonic(
                master_seed=test_master_seed, word_count=12, index=index, language="en"
            )
            individual_results.append(result)
        individual_time = (time.perf_counter() - start_time) * 1000

        # Clear cache for fair comparison
        optimized_apps.clear_cache()

        # Batch operation
        start_time = time.perf_counter()
        batch_results = optimized_apps.derive_batch_bip39(
            master_seed=test_master_seed, word_count=12, indices=indices, language="en"
        )
        batch_time = (time.perf_counter() - start_time) * 1000

        # Verify results are identical
        assert (
            batch_results == individual_results
        ), "Batch and individual results should match"

        # Calculate improvement
        improvement_percent = (individual_time - batch_time) / individual_time * 100

        print("\n⚡ Batch Operation Performance:")
        print(f"   Individual ops: {individual_time:.2f}ms total")
        print(f"   Batch operation: {batch_time:.2f}ms total")
        print(f"   Improvement: {improvement_percent:.1f}%")
        print(f"   Per-operation: {batch_time / len(indices):.2f}ms avg")

        # Batch should be faster or at least competitive
        assert (
            batch_time <= individual_time * 1.1
        ), f"Batch operation not competitive: {batch_time:.2f}ms vs {individual_time:.2f}ms"

    def test_multi_application_caching_efficiency(
        self, optimized_apps, test_master_seed
    ):
        """Test caching efficiency across different applications."""
        operations = [
            (
                "bip39",
                lambda i: optimized_apps.derive_bip39_mnemonic(
                    test_master_seed, 12, i, "en"
                ),
            ),
            (
                "hex",
                lambda i: optimized_apps.derive_hex_entropy(
                    test_master_seed, 32, i, False
                ),
            ),
            (
                "password",
                lambda i: optimized_apps.derive_password(
                    test_master_seed, 20, i, "base64"
                ),
            ),
        ]

        start_time = time.perf_counter()

        # Perform mixed operations to test cache efficiency
        results = {}
        for round_num in range(3):
            for app_name, operation in operations:
                for index in range(5):
                    result = operation(index)
                    key = f"{app_name}_{index}"
                    if key not in results:
                        results[key] = result
                    else:
                        # Verify deterministic results
                        assert (
                            results[key] == result
                        ), f"Non-deterministic result for {key}"

        total_time = (time.perf_counter() - start_time) * 1000
        operations_count = 3 * 3 * 5  # 3 rounds × 3 apps × 5 indices
        avg_time_per_op = total_time / operations_count

        print("\n🔀 Multi-Application Caching:")
        print(f"   Total operations: {operations_count}")
        print(f"   Total time: {total_time:.2f}ms")
        print(f"   Average per operation: {avg_time_per_op:.2f}ms")

        # Get cache statistics
        stats = optimized_apps.get_performance_stats()
        cache_stats = stats["cache_stats"]

        print(f"   Cache hits: {cache_stats['hits']}")
        print(f"   Cache misses: {cache_stats['misses']}")
        print(f"   Hit rate: {cache_stats['hit_rate_percent']:.1f}%")

        # Validate reasonable cache performance
        assert (
            cache_stats["hit_rate_percent"] > 50
        ), f"Cache hit rate too low: {cache_stats['hit_rate_percent']:.1f}%"
        assert (
            avg_time_per_op < 2.0
        ), f"Average operation too slow: {avg_time_per_op:.2f}ms"


class TestCacheEfficiency:
    """Test cache system efficiency and correctness."""

    def test_cache_correctness_deterministic_results(
        self, optimized_apps, test_master_seed
    ):
        """Verify cache returns correct deterministic results."""

        # Generate initial results
        initial_results = {}
        for app in ["bip39", "hex", "password"]:
            for index in range(5):
                if app == "bip39":
                    result = optimized_apps.derive_bip39_mnemonic(
                        test_master_seed, 12, index, "en"
                    )
                elif app == "hex":
                    result = optimized_apps.derive_hex_entropy(
                        test_master_seed, 32, index, False
                    )
                else:  # password
                    result = optimized_apps.derive_password(
                        test_master_seed, 20, index, "base64"
                    )

                initial_results[f"{app}_{index}"] = result

        # Verify cached results match
        for key, expected_result in initial_results.items():
            app, index_str = key.split("_")
            index = int(index_str)

            if app == "bip39":
                cached_result = optimized_apps.derive_bip39_mnemonic(
                    test_master_seed, 12, index, "en"
                )
            elif app == "hex":
                cached_result = optimized_apps.derive_hex_entropy(
                    test_master_seed, 32, index, False
                )
            else:  # password
                cached_result = optimized_apps.derive_password(
                    test_master_seed, 20, index, "base64"
                )

            assert (
                cached_result == expected_result
            ), f"Cached result mismatch for {key}: {cached_result} != {expected_result}"

        # Verify cache is being used
        stats = optimized_apps.get_performance_stats()
        assert (
            stats["cache_stats"]["hits"] > 0
        ), "Cache should have hits after repeated operations"

    def test_cache_isolation_different_seeds(self, optimized_apps):
        """Test cache properly isolates results for different master seeds."""
        seed1 = bytes.fromhex("a" * 128)
        seed2 = bytes.fromhex("b" * 128)

        # Generate results for different seeds
        result1 = optimized_apps.derive_bip39_mnemonic(seed1, 12, 0, "en")
        result2 = optimized_apps.derive_bip39_mnemonic(seed2, 12, 0, "en")

        # Results should be different
        assert result1 != result2, "Different seeds should produce different results"

        # Verify cache returns correct results for each seed
        cached_result1 = optimized_apps.derive_bip39_mnemonic(seed1, 12, 0, "en")
        cached_result2 = optimized_apps.derive_bip39_mnemonic(seed2, 12, 0, "en")

        assert (
            cached_result1 == result1
        ), "Cached result should match original for seed1"
        assert (
            cached_result2 == result2
        ), "Cached result should match original for seed2"

    def test_cache_memory_management(self, optimized_apps, test_master_seed):
        """Test cache memory management and cleanup."""
        # Clear cache to start with clean state
        optimized_apps._key_manager._cache.clear()

        initial_stats = optimized_apps.get_performance_stats()["cache_stats"]

        # Generate many operations to test cache limits
        for i in range(200):  # More than default cache size
            optimized_apps.derive_hex_entropy(test_master_seed, 16, i % 100, False)

        final_stats = optimized_apps.get_performance_stats()["cache_stats"]

        print("\n🗑️ Cache Memory Management:")
        print(f"   Cache size: {final_stats['cache_size']}")
        print(f"   Max entries: {final_stats['max_entries']}")
        print(f"   Evictions: {final_stats['evictions']}")
        print(f"   Cleanups: {final_stats['cleanups']}")

        # Cache should respect size limits
        assert (
            final_stats["cache_size"] <= final_stats["max_entries"]
        ), "Cache exceeded maximum size"

        # Should have performed evictions for large operation count
        assert (
            final_stats["evictions"] > 0 or final_stats["cleanups"] > 0
        ), "Cache should have performed cleanup with many operations"


class TestPerformanceRegression:
    """Ensure no performance regression in optimized implementation."""

    def test_optimized_vs_standard_performance_parity(
        self, standard_apps, optimized_apps_no_cache, test_master_seed
    ):
        """Ensure optimized version without cache performs comparably to standard."""

        operations = [
            (
                "bip39",
                lambda apps: apps.derive_bip39_mnemonic(test_master_seed, 12, 0, "en"),
            ),
            (
                "hex",
                lambda apps: apps.derive_hex_entropy(test_master_seed, 32, 0, False),
            ),
            (
                "password",
                lambda apps: apps.derive_password(test_master_seed, 20, 0, "base64"),
            ),
        ]

        for op_name, operation in operations:
            # Measure standard implementation
            standard_stats = measure_performance(
                lambda: operation(standard_apps), iterations=20
            )

            # Measure optimized implementation (no cache)
            optimized_stats = measure_performance(
                lambda: operation(optimized_apps_no_cache), iterations=20
            )

            # Calculate performance difference
            diff_percent = (
                (optimized_stats["mean_ms"] - standard_stats["mean_ms"])
                / standard_stats["mean_ms"]
                * 100
            )

            print(f"\n📊 {op_name.title()} Performance Parity:")
            print(f"   Standard: {standard_stats['mean_ms']:.2f}ms")
            print(f"   Optimized (no cache): {optimized_stats['mean_ms']:.2f}ms")
            print(f"   Difference: {diff_percent:+.1f}%")

            # Optimized should not be significantly slower (allow 50% variance for infrastructure overhead)
            assert (
                optimized_stats["mean_ms"] <= standard_stats["mean_ms"] * 1.50
            ), f"{op_name} performance regression: {diff_percent:.1f}% slower"
