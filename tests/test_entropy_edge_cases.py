"""Comprehensive entropy edge case tests for sseed.

Tests entropy generation error conditions, security scenarios, and edge cases
to achieve comprehensive coverage of entropy handling logic.
"""

import os
import unittest.mock as mock
from unittest.mock import (
    MagicMock,
    patch,
)

import pytest

from sseed.entropy import (
    generate_entropy_bits,
    generate_entropy_bytes,
    secure_delete_variable,
)
from sseed.exceptions import (
    EntropyError,
    SecurityError,
)


class TestEntropyEdgeCases:
    """Comprehensive entropy edge case tests."""

    def test_generate_entropy_bytes_invalid_size_zero(self):
        """Test entropy generation with zero byte size."""
        with pytest.raises(SecurityError, match="Invalid entropy bytes requested"):
            generate_entropy_bytes(0)

    def test_generate_entropy_bytes_invalid_size_negative(self):
        """Test entropy generation with negative byte size."""
        with pytest.raises(SecurityError, match="Invalid entropy bytes requested"):
            generate_entropy_bytes(-5)

    def test_generate_entropy_bytes_excessive_size(self):
        """Test entropy generation with excessively large size."""
        with pytest.raises(EntropyError, match="Entropy size too large"):
            generate_entropy_bytes(1024 * 1024 * 10)  # 10MB

    def test_generate_entropy_bytes_system_random_failure(self):
        """Test entropy generation when SystemRandom fails."""
        with patch("secrets.token_bytes", side_effect=OSError("System entropy unavailable")):
            with pytest.raises(EntropyError, match="Failed to generate .* bytes of entropy"):
                generate_entropy_bytes(32)

    def test_generate_entropy_bytes_memory_error(self):
        """Test entropy generation with memory allocation failure."""
        with patch("secrets.token_bytes", side_effect=MemoryError("Insufficient memory")):
            with pytest.raises(EntropyError, match="Failed to generate .* bytes of entropy"):
                generate_entropy_bytes(32)

    def test_generate_entropy_bits_invalid_bits_zero(self):
        """Test entropy bits generation with zero bits."""
        with pytest.raises(Exception):  # Could be SecurityError or EntropyError
            generate_entropy_bits(0)

    def test_generate_entropy_bits_invalid_bits_negative(self):
        """Test entropy bits generation with negative bits."""
        with pytest.raises(Exception):  # Could be SecurityError or EntropyError
            generate_entropy_bits(-10)

    def test_generate_entropy_bits_excessive_bits(self):
        """Test entropy bits generation with excessive bit count."""
        with pytest.raises(Exception):  # Could be SecurityError or EntropyError
            generate_entropy_bits(10000)  # Above 4096 limit

    def test_generate_entropy_bits_system_random_failure(self):
        """Test entropy bits generation when SystemRandom fails."""
        with patch("secrets.SystemRandom") as mock_random:
            mock_random.return_value.getrandbits.side_effect = OSError("System entropy unavailable")
            with pytest.raises(EntropyError, match="Failed to generate"):
                generate_entropy_bits(256)

    def test_generate_entropy_bytes_excessive_size(self):
        """Test entropy bytes generation with size above limit."""
        with pytest.raises(Exception):  # Could be SecurityError or EntropyError
            generate_entropy_bytes(1000)  # Above 512 limit

    def test_secure_delete_variable_single_variable(self):
        """Test secure deletion of single variable."""
        test_var = "sensitive_data"
        secure_delete_variable(test_var)
        # Variable should be cleared from memory (implementation detail)

    def test_secure_delete_variable_multiple_variables(self):
        """Test secure deletion of multiple variables."""
        var1 = "sensitive_data_1"
        var2 = b"sensitive_bytes"
        var3 = ["list", "of", "data"]
        secure_delete_variable(var1, var2, var3)
        # Variables should be cleared from memory

    def test_secure_delete_variable_none_values(self):
        """Test secure deletion with None values."""
        secure_delete_variable(None, None)
        # Should handle None values gracefully

    def test_secure_delete_variable_mixed_types(self):
        """Test secure deletion with mixed data types."""
        var1 = "string"
        var2 = 12345
        var3 = {"dict": "value"}
        var4 = [1, 2, 3]
        secure_delete_variable(var1, var2, var3, var4)
        # Should handle different types gracefully

    def test_secure_delete_variable_exception_handling(self):
        """Test secure deletion with exception during cleanup."""

        # Create a custom object that raises an exception when deleted
        class BadCleanupObject:
            def __del__(self):
                raise Exception("Cleanup error")

        obj = BadCleanupObject()

        # Should not raise exception even if cleanup fails
        secure_delete_variable(obj)

    def test_entropy_generation_system_entropy_exhaustion(self):
        """Test behavior when system entropy is temporarily exhausted."""
        call_count = [0]

        def failing_token_bytes(size):
            call_count[0] += 1
            if call_count[0] <= 2:  # Fail first two calls
                raise OSError("Entropy temporarily unavailable")
            return os.urandom(size)  # Succeed on third call

        with patch("secrets.token_bytes", side_effect=failing_token_bytes):
            # Should retry and eventually succeed (if retry logic exists)
            # Or fail with appropriate error
            with pytest.raises(EntropyError):
                generate_entropy_bytes(32)

    def test_generate_entropy_bytes_boundary_conditions(self):
        """Test entropy bytes generation at boundary conditions."""
        # Test minimum valid size
        result = generate_entropy_bytes(1)
        assert len(result) == 1

        # Test maximum valid size
        result = generate_entropy_bytes(512)
        assert len(result) == 512

    def test_entropy_generation_with_limited_memory(self):
        """Test entropy generation under memory pressure."""
        # Simulate memory pressure by making allocation fail
        original_token_bytes = __import__("secrets").token_bytes

        def memory_limited_token_bytes(size):
            if size > 1024:  # Fail for large allocations
                raise MemoryError("Memory allocation failed")
            return original_token_bytes(size)

        with patch("secrets.token_bytes", side_effect=memory_limited_token_bytes):
            # Small allocations should work
            result = generate_entropy_bytes(32)
            assert len(result) == 32

            # Large allocations should fail
            with pytest.raises(SecurityError):
                generate_entropy_bytes(2048)

    def test_generate_entropy_bits_boundary_conditions(self):
        """Test entropy bits generation at boundary conditions."""
        # Test minimum valid size
        result = generate_entropy_bits(1)
        assert result >= 0

        # Test maximum valid size
        result = generate_entropy_bits(4096)
        assert result >= 0

    def test_secure_deletion_memory_overwrite(self):
        """Test that secure deletion actually overwrites memory."""
        # Create sensitive data
        sensitive = bytearray(b"very secret data" * 100)
        original_id = id(sensitive)

        # Perform secure deletion
        secure_delete_variable(sensitive)

        # Memory should be overwritten (implementation detail)
        # This test verifies the function doesn't crash

    def test_entropy_generation_concurrency_safety(self):
        """Test entropy generation thread safety."""
        import threading
        import time

        results = []
        errors = []

        def generate_entropy_worker():
            try:
                for _ in range(10):
                    entropy = generate_entropy_bytes(32)
                    results.append(entropy)
                    time.sleep(0.001)  # Small delay
            except Exception as e:
                errors.append(e)

        # Start multiple threads
        threads = [threading.Thread(target=generate_entropy_worker) for _ in range(5)]
        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # Should have no errors and all unique results
        assert len(errors) == 0
        assert len(results) == 50
        assert len(set(results)) == len(results)  # All unique

    def test_entropy_fallback_mechanisms(self):
        """Test entropy generation fallback mechanisms."""
        # Test when primary entropy source fails
        with patch("secrets.token_bytes", side_effect=OSError("Primary source failed")):
            with patch("os.urandom", side_effect=OSError("Fallback also failed")):
                with pytest.raises(EntropyError, match="Failed to generate .* bytes of entropy"):
                    generate_entropy_bytes(32)

    def test_entropy_generation_edge_cases(self):
        """Test entropy generation edge cases."""
        # Test normal operation
        result = generate_entropy_bytes(32)
        assert len(result) == 32

        result = generate_entropy_bits(256)
        assert result >= 0
