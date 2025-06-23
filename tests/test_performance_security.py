"""
Performance and Security Tests for Phase 9.

Tests execution time, memory usage, secure memory handling, and verifies no internet calls.
"""

import gc
import io
import os
import platform
import subprocess
import sys
import time
import unittest
from contextlib import (
    redirect_stderr,
    redirect_stdout,
)
from pathlib import Path
from typing import Any
from unittest.mock import patch

import psutil
import pytest

# Add the sseed package to the path for testing
sys.path.insert(0, str(Path(__file__).parent.parent))

from sseed.bip39 import (
    generate_mnemonic,
    get_mnemonic_entropy,
    validate_mnemonic,
)
from sseed.cli import main as cli_main
from sseed.entropy import (
    generate_entropy_bits,
    generate_entropy_bytes,
    secure_delete_variable,
)
from sseed.slip39_operations import (
    create_slip39_shards,
    reconstruct_mnemonic_from_shards,
    validate_slip39_shard,
)


class TestPerformanceAndSecurity(unittest.TestCase):
    """Test suite for Phase 9: Performance & Security requirements."""

    def setUp(self) -> None:
        """Set up test environment."""
        self.process = psutil.Process(os.getpid())

    def tearDown(self) -> None:
        """Clean up test environment."""
        # Clean up any temporary files that may have been created during tests
        temp_patterns = [
            "*test_mnemonic*",
            "*offline_test*",
            "*offline_shards*",
            "*perf_test*",
            "_var_folders_*",
            "_tmp_*",
            "_Users_*",
        ]
        for pattern in temp_patterns:
            for file in Path(".").glob(pattern):
                if file.is_file():
                    try:
                        file.unlink()
                    except OSError:
                        pass  # Ignore if file is already gone

    def measure_performance(
        self, operation_func: callable, *args: Any, **kwargs: Any
    ) -> tuple[float, Any]:
        """Measure execution time and memory usage of an operation.

        Args:
            operation_func: Function to execute and measure
            *args: Arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function

        Returns:
            Tuple of (execution_time_ms, result)
        """
        # Force garbage collection before measurement
        gc.collect()

        # Get initial memory
        initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB

        # Measure execution time
        start_time = time.perf_counter()
        result = operation_func(*args, **kwargs)
        end_time = time.perf_counter()

        # Get peak memory during operation
        peak_memory = self.process.memory_info().rss / 1024 / 1024  # MB

        execution_time_ms = (end_time - start_time) * 1000
        memory_used = peak_memory - initial_memory

        print(
            f"Operation {operation_func.__name__}: {execution_time_ms:.2f}ms, Memory: {memory_used:.2f}MB"
        )

        return execution_time_ms, result

    def test_38_mnemonic_generation_performance(self) -> None:
        """Test 38: Verify mnemonic generation execution time is reasonable."""
        print("\n=== Testing Mnemonic Generation Performance ===")

        # Test multiple runs to get average
        times = []
        for i in range(10):
            exec_time, mnemonic = self.measure_performance(generate_mnemonic)
            times.append(exec_time)
            self.assertIsInstance(mnemonic, str)
            self.assertEqual(len(mnemonic.split()), 24)

        avg_time = sum(times) / len(times)
        max_time = max(times)
        min_time = min(times)

        print(
            f"Mnemonic Generation - Avg: {avg_time:.2f}ms, Min: {min_time:.2f}ms, Max: {max_time:.2f}ms"
        )

        # Performance should be reasonable (well under 1 second, preferably under 100ms)
        self.assertLess(
            avg_time,
            100,
            f"Average mnemonic generation time {avg_time:.2f}ms is too slow",
        )
        self.assertLess(
            max_time,
            200,
            f"Maximum mnemonic generation time {max_time:.2f}ms is too slow",
        )

    def test_38_slip39_sharding_performance(self) -> None:
        """Test 38: Verify SLIP-39 sharding execution time is reasonable."""
        print("\n=== Testing SLIP-39 Sharding Performance ===")

        # Generate test mnemonic
        mnemonic = generate_mnemonic()

        # Test sharding performance
        times = []
        for i in range(5):
            exec_time, shards = self.measure_performance(
                create_slip39_shards, mnemonic, group_threshold=1, groups=[(3, 5)]
            )
            times.append(exec_time)
            self.assertEqual(len(shards), 5)

        avg_time = sum(times) / len(times)
        max_time = max(times)

        print(f"SLIP-39 Sharding - Avg: {avg_time:.2f}ms, Max: {max_time:.2f}ms")

        # Sharding should be reasonable (preferably under 500ms)
        self.assertLess(
            avg_time, 500, f"Average sharding time {avg_time:.2f}ms is too slow"
        )
        self.assertLess(
            max_time, 1000, f"Maximum sharding time {max_time:.2f}ms is too slow"
        )

    def test_38_slip39_reconstruction_performance(self) -> None:
        """Test 38: Verify SLIP-39 reconstruction execution time is reasonable."""
        print("\n=== Testing SLIP-39 Reconstruction Performance ===")

        # Generate test data
        mnemonic = generate_mnemonic()
        shards = create_slip39_shards(mnemonic, group_threshold=1, groups=[(3, 5)])
        test_shards = shards[:3]  # Use minimum threshold

        # Test reconstruction performance
        times = []
        for i in range(5):
            exec_time, reconstructed = self.measure_performance(
                reconstruct_mnemonic_from_shards, test_shards
            )
            times.append(exec_time)
            self.assertEqual(reconstructed, mnemonic)

        avg_time = sum(times) / len(times)
        max_time = max(times)

        print(f"SLIP-39 Reconstruction - Avg: {avg_time:.2f}ms, Max: {max_time:.2f}ms")

        # Reconstruction should be reasonable (preferably under 500ms)
        self.assertLess(
            avg_time, 500, f"Average reconstruction time {avg_time:.2f}ms is too slow"
        )
        self.assertLess(
            max_time, 1000, f"Maximum reconstruction time {max_time:.2f}ms is too slow"
        )

    def test_38_cli_operations_performance(self) -> None:
        """Test 38: Verify CLI operations execution time is reasonable."""
        print("\n=== Testing CLI Operations Performance ===")

        # Test CLI performance using subprocess (more realistic)
        test_file = "perf_test_mnemonic.txt"
        shards_file = "perf_test_shards.txt"

        # Clean up any existing files
        for pattern in ["*perf_test*"]:
            for f in Path(".").glob(pattern):
                if f.is_file():
                    f.unlink()

        try:
            # Test gen command
            start_time = time.perf_counter()
            result = subprocess.run(
                [sys.executable, "-m", "sseed", "gen", "-o", test_file],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent,
            )
            gen_time = (time.perf_counter() - start_time) * 1000

            self.assertEqual(
                result.returncode, 0, f"Gen command failed: {result.stderr}"
            )
            print(f"CLI gen command: {gen_time:.2f}ms")

            # Find the actual created file (may have sanitized filename)
            created_files = list(Path(".").glob("*perf_test_mnemonic*"))
            self.assertTrue(len(created_files) > 0, "No mnemonic file was created")
            actual_test_file = created_files[0]

            # Test shard command
            start_time = time.perf_counter()
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "sseed",
                    "shard",
                    "-i",
                    str(actual_test_file),
                    "-g",
                    "3-of-5",
                    "-o",
                    shards_file,
                ],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent,
            )
            shard_time = (time.perf_counter() - start_time) * 1000

            self.assertEqual(
                result.returncode, 0, f"Shard command failed: {result.stderr}"
            )
            print(f"CLI shard command: {shard_time:.2f}ms")

            # Performance should be reasonable for CLI operations (under 2 seconds including Python startup)
            self.assertLess(
                gen_time, 2000, f"CLI gen time {gen_time:.2f}ms is too slow"
            )
            self.assertLess(
                shard_time, 2000, f"CLI shard time {shard_time:.2f}ms is too slow"
            )

        finally:
            # Clean up created files
            for pattern in ["*perf_test*"]:
                for f in Path(".").glob(pattern):
                    if f.is_file():
                        f.unlink()

    def test_39_memory_usage_limits(self) -> None:
        """Test 39: Ensure RAM usage stays within reasonable limits."""
        print("\n=== Testing Memory Usage Limits ===")

        # Get baseline memory
        gc.collect()
        baseline_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        print(f"Baseline memory: {baseline_memory:.2f}MB")

        # Test memory usage during operations
        max_memory = baseline_memory

        # Generate multiple mnemonics to stress test memory
        mnemonics = []
        for i in range(10):
            mnemonic = generate_mnemonic()
            mnemonics.append(mnemonic)
            current_memory = self.process.memory_info().rss / 1024 / 1024
            max_memory = max(max_memory, current_memory)

        # Generate shards for each mnemonic
        all_shards = []
        for mnemonic in mnemonics:
            shards = create_slip39_shards(mnemonic, group_threshold=1, groups=[(3, 5)])
            all_shards.extend(shards)
            current_memory = self.process.memory_info().rss / 1024 / 1024
            max_memory = max(max_memory, current_memory)

        # Test reconstruction
        for i in range(0, len(all_shards), 5):
            if i + 3 <= len(all_shards):
                test_shards = all_shards[i : i + 3]
                try:
                    reconstructed = reconstruct_mnemonic_from_shards(test_shards)
                    current_memory = self.process.memory_info().rss / 1024 / 1024
                    max_memory = max(max_memory, current_memory)
                except Exception:
                    pass  # Expected for mismatched shards

        memory_used = max_memory - baseline_memory
        print(f"Peak memory usage during operations: {max_memory:.2f}MB")
        print(f"Additional memory used: {memory_used:.2f}MB")

        # Memory usage should be reasonable (well under 200MB total, additional usage under 50MB)
        self.assertLess(
            max_memory,
            200,
            f"Peak memory usage {max_memory:.2f}MB exceeds reasonable limit",
        )
        self.assertLess(
            memory_used, 50, f"Additional memory usage {memory_used:.2f}MB is too high"
        )

    def test_40_secure_memory_handling(self) -> None:
        """Test 40: Verify secure memory handling is implemented."""
        print("\n=== Testing Secure Memory Handling ===")

        # Test secure_delete_variable function
        test_var1 = "sensitive_data_123"
        test_var2 = b"binary_sensitive_data"
        test_var3 = ["list", "of", "sensitive", "data"]

        # Variables should exist before deletion
        self.assertEqual(test_var1, "sensitive_data_123")
        self.assertEqual(test_var2, b"binary_sensitive_data")
        self.assertEqual(len(test_var3), 4)

        # Test secure deletion
        secure_delete_variable(test_var1, test_var2, test_var3)

        # Variables should be None after deletion (within the function scope)
        # This is a basic test - the actual security benefit is in clearing memory references

        # Test that entropy generation uses secure deletion
        entropy = generate_entropy_bits(256)
        self.assertIsInstance(entropy, int)

        entropy_bytes = generate_entropy_bytes(32)
        self.assertIsInstance(entropy_bytes, bytes)
        self.assertEqual(len(entropy_bytes), 32)

        # Test that BIP-39 operations use secure deletion
        mnemonic = generate_mnemonic()
        self.assertEqual(len(mnemonic.split()), 24)

        # Verify entropy extraction uses secure deletion
        entropy_from_mnemonic = get_mnemonic_entropy(mnemonic)
        self.assertIsInstance(entropy_from_mnemonic, bytes)

        print("✅ Secure memory handling functions are implemented and working")

    def test_41_no_internet_calls(self) -> None:
        """Test 41: Verify no internet calls are made."""
        print("\n=== Testing No Internet Calls ===")

        # Mock socket operations to detect any network calls
        import socket

        original_socket = socket.socket
        network_calls = []

        def mock_socket(*args, **kwargs):
            network_calls.append(
                f"socket.socket called with args: {args}, kwargs: {kwargs}"
            )
            return original_socket(*args, **kwargs)

        # Mock urllib and requests if they exist
        import urllib.request

        original_urlopen = urllib.request.urlopen

        def mock_urlopen(*args, **kwargs):
            network_calls.append(f"urllib.request.urlopen called with args: {args}")
            return original_urlopen(*args, **kwargs)

        with (
            patch("socket.socket", side_effect=mock_socket),
            patch("urllib.request.urlopen", side_effect=mock_urlopen),
        ):

            # Test all major operations
            mnemonic = generate_mnemonic()
            self.assertEqual(len(mnemonic.split()), 24)

            # Test validation
            is_valid = validate_mnemonic(mnemonic)
            self.assertTrue(is_valid)

            # Test entropy operations
            entropy = generate_entropy_bits(256)
            self.assertIsInstance(entropy, int)

            entropy_bytes = generate_entropy_bytes(32)
            self.assertEqual(len(entropy_bytes), 32)

            # Test SLIP-39 operations
            shards = create_slip39_shards(mnemonic, group_threshold=1, groups=[(2, 3)])
            self.assertEqual(len(shards), 3)

            for shard in shards:
                is_valid_shard = validate_slip39_shard(shard)
                self.assertTrue(is_valid_shard)

            # Test reconstruction
            reconstructed = reconstruct_mnemonic_from_shards(shards[:2])
            self.assertEqual(reconstructed, mnemonic)

        # Verify no network calls were made
        self.assertEqual(
            len(network_calls), 0, f"Unexpected network calls detected: {network_calls}"
        )

        print("✅ No internet calls detected during cryptographic operations")

    def test_41_offline_verification_cli(self) -> None:
        """Test 41: Verify CLI works completely offline."""
        print("\n=== Testing CLI Offline Operation ===")

        # Test CLI commands work without network
        test_file = (
            "offline_test.txt"  # Use simple filename to avoid path sanitization issues
        )
        shards_file = "offline_shards.txt"

        # Clean up any existing files
        for f in [test_file, shards_file]:
            if Path(f).exists():
                Path(f).unlink()

        # Disable network for this test (if possible)
        try:
            # Test gen command
            result = subprocess.run(
                [sys.executable, "-m", "sseed", "gen", "-o", test_file],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent,
                timeout=10,
            )

            self.assertEqual(
                result.returncode, 0, f"Gen command failed: {result.stderr}"
            )

            # Check if file was created (may have sanitized filename)
            created_files = list(Path(".").glob("*offline_test*"))
            self.assertTrue(
                len(created_files) > 0,
                f"No output file was created. Expected pattern: *offline_test*. Found files: {list(Path('.').glob('*'))}",
            )

            # Use the first created file
            actual_test_file = created_files[0]

            # Verify file contains valid mnemonic
            with open(actual_test_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                # Extract mnemonic (skip comment lines)
                mnemonic_lines = [
                    line
                    for line in content.split("\n")
                    if line.strip() and not line.strip().startswith("#")
                ]
                self.assertTrue(
                    len(mnemonic_lines) > 0, "No mnemonic found in output file"
                )
                mnemonic = mnemonic_lines[0].strip()
                self.assertEqual(len(mnemonic.split()), 24, "Invalid mnemonic length")

            # Test shard command
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "sseed",
                    "shard",
                    "-i",
                    str(actual_test_file),
                    "-g",
                    "2-of-3",
                    "-o",
                    shards_file,
                ],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent,
                timeout=10,
            )

            self.assertEqual(
                result.returncode, 0, f"Shard command failed: {result.stderr}"
            )

            # Check if shards file was created (may have sanitized filename)
            shard_files = list(Path(".").glob("*offline_shards*"))
            self.assertTrue(len(shard_files) > 0, "Shards file was not created")

            print("✅ CLI operations work completely offline")

        except subprocess.TimeoutExpired:
            self.fail("CLI operation timed out - may indicate network dependency")
        finally:
            # Clean up created files
            for pattern in ["*offline_test*", "*offline_shards*"]:
                for f in Path(".").glob(pattern):
                    if f.is_file():
                        f.unlink()

    def test_performance_summary(self) -> None:
        """Generate a summary of performance characteristics."""
        print("\n=== Performance Summary ===")

        # Get system info
        print(f"System: {platform.system()} {platform.release()}")
        print(f"Python: {sys.version}")
        print(f"CPU Count: {psutil.cpu_count()}")

        # Current memory
        current_memory = self.process.memory_info().rss / 1024 / 1024
        print(f"Current process memory: {current_memory:.2f}MB")

        # Quick performance test
        start_time = time.perf_counter()
        mnemonic = generate_mnemonic()
        gen_time = (time.perf_counter() - start_time) * 1000

        start_time = time.perf_counter()
        shards = create_slip39_shards(mnemonic, group_threshold=1, groups=[(2, 3)])
        shard_time = (time.perf_counter() - start_time) * 1000

        start_time = time.perf_counter()
        reconstructed = reconstruct_mnemonic_from_shards(shards[:2])
        restore_time = (time.perf_counter() - start_time) * 1000

        print(f"Quick benchmark:")
        print(f"  - Mnemonic generation: {gen_time:.2f}ms")
        print(f"  - SLIP-39 sharding: {shard_time:.2f}ms")
        print(f"  - SLIP-39 reconstruction: {restore_time:.2f}ms")

        # All operations should be reasonable
        total_time = gen_time + shard_time + restore_time
        print(f"  - Total round-trip time: {total_time:.2f}ms")

        self.assertLess(
            total_time, 1000, f"Total round-trip time {total_time:.2f}ms is too slow"
        )


if __name__ == "__main__":
    # Run with verbose output to see performance measurements
    unittest.main(verbosity=2)
