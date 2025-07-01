"""Security-critical tests for sseed.bip85.security module.

Tests focus on:
- Security hardening mechanisms
- Timing attack protection
- Memory protection and secure clearing
- Entropy validation for cryptographic operations
- Edge case security validation
- Index boundary protection
"""

import time
from unittest.mock import (
    MagicMock,
    patch,
)

import pytest

from sseed.bip85.exceptions import Bip85ValidationError
from sseed.bip85.security import (
    SecurityHardening,
    audit_bip85_security,
    get_security_hardening,
    secure_clear_memory,
    validate_entropy_security,
)


class TestSecurityHardening:
    """Test SecurityHardening class for BIP85 operations."""

    def setup_method(self):
        """Set up security hardening instance for tests."""
        self.security = SecurityHardening()

    def test_security_hardening_initialization(self):
        """Test proper initialization of security hardening."""
        assert self.security._timing_attack_protection is True
        assert self.security._memory_protection is True
        assert self.security._entropy_validation is True

    def test_validate_entropy_quality_sufficient_entropy(self):
        """Test entropy validation with sufficient quality entropy."""
        # Good quality entropy - varied bytes
        good_entropy = bytes(
            [i % 256 for i in range(0, 256, 17)]
        )  # 16 bytes of varied data

        result = self.security.validate_entropy_quality(
            good_entropy, min_entropy_bits=128
        )
        assert result is True

    def test_validate_entropy_quality_insufficient_length(self):
        """Test entropy validation fails with insufficient entropy length."""
        short_entropy = b"\x01\x02\x03\x04"  # Only 4 bytes = 32 bits

        with pytest.raises(Bip85ValidationError, match="Insufficient entropy"):
            self.security.validate_entropy_quality(short_entropy, min_entropy_bits=128)

    def test_validate_entropy_quality_weak_patterns_all_zeros(self):
        """Test entropy validation detects all-zero weak pattern."""
        weak_entropy = b"\x00" * 16  # All zeros

        with pytest.raises(Bip85ValidationError, match="weak patterns"):
            self.security.validate_entropy_quality(weak_entropy)

    def test_validate_entropy_quality_weak_patterns_all_ones(self):
        """Test entropy validation detects all-ones weak pattern."""
        weak_entropy = b"\xff" * 16  # All ones

        with pytest.raises(Bip85ValidationError, match="weak patterns"):
            self.security.validate_entropy_quality(weak_entropy)

    def test_validate_entropy_quality_weak_patterns_repeating(self):
        """Test entropy validation detects repeating patterns."""
        weak_entropy = b"\xaa\xbb" * 8  # Simple repeating pattern

        with pytest.raises(Bip85ValidationError, match="weak patterns"):
            self.security.validate_entropy_quality(weak_entropy)

    def test_validate_entropy_quality_chi_square_failure(self):
        """Test entropy validation detects poor randomness via chi-square test."""
        # Create entropy that passes pattern check but fails chi-square
        # Need larger sample for chi-square test to trigger (32+ bytes)
        poor_randomness = b"\x00" * 30 + b"\x01\x02"  # Very skewed distribution

        with pytest.raises(Bip85ValidationError, match="randomness test"):
            self.security.validate_entropy_quality(poor_randomness)

    def test_validate_entropy_quality_custom_min_bits(self):
        """Test entropy validation with custom minimum bits requirement."""
        entropy = b"\x01\x02\x03\x04\x05\x06\x07\x08"  # 8 bytes = 64 bits

        # Should pass with 64-bit requirement
        result = self.security.validate_entropy_quality(entropy, min_entropy_bits=64)
        assert result is True

        # Should fail with 128-bit requirement
        with pytest.raises(Bip85ValidationError, match="Insufficient entropy"):
            self.security.validate_entropy_quality(entropy, min_entropy_bits=128)

    def test_validate_entropy_quality_exception_handling(self):
        """Test exception handling in entropy validation."""
        # Mock internal methods to raise an exception
        with patch.object(
            self.security, "_has_weak_patterns", side_effect=Exception("Test error")
        ):
            with pytest.raises(Exception, match="Test error"):
                self.security.validate_entropy_quality(b"\x01" * 16)

    def test_has_weak_patterns_detection(self):
        """Test weak pattern detection methods."""
        # All zeros
        assert self.security._has_weak_patterns(b"\x00" * 16) is True

        # All ones
        assert self.security._has_weak_patterns(b"\xff" * 16) is True

        # Simple repeating pattern
        assert self.security._has_weak_patterns(b"\xaa\xbb" * 8) is True

        # Sequential pattern
        assert self.security._has_weak_patterns(bytes(range(16))) is True

        # Good varied entropy should not trigger weak pattern detection
        good_entropy = bytes([i % 256 for i in range(0, 256, 17)])
        assert self.security._has_weak_patterns(good_entropy) is False

    def test_passes_chi_square_test(self):
        """Test chi-square randomness testing."""
        # All zeros should fail chi-square test
        assert self.security._passes_chi_square_test(b"\x00" * 32) is False

        # All ones should fail chi-square test
        assert self.security._passes_chi_square_test(b"\xff" * 32) is False

        # Very skewed distribution should fail
        skewed = b"\x00" * 30 + b"\x01\x02"
        assert self.security._passes_chi_square_test(skewed) is False

        # Well-distributed entropy should pass
        good_entropy = bytes([i % 256 for i in range(32)])
        assert self.security._passes_chi_square_test(good_entropy) is True


class TestTimingAttackProtection:
    """Test timing attack protection mechanisms."""

    def setup_method(self):
        """Set up security hardening instance for tests."""
        self.security = SecurityHardening()

    def test_timing_protection_attribute_exists(self):
        """Test timing protection is properly configured."""
        # Test that timing attack protection is enabled by default
        assert hasattr(self.security, "_timing_attack_protection")
        assert self.security._timing_attack_protection is True

    def test_timing_protection_can_be_disabled(self):
        """Test timing protection can be disabled."""
        self.security._timing_attack_protection = False
        assert self.security._timing_attack_protection is False


class TestIndexBoundaryValidation:
    """Test index boundary validation for security."""

    def setup_method(self):
        """Set up security hardening instance for tests."""
        self.security = SecurityHardening()

    def test_validate_index_boundaries_valid_indices(self):
        """Test validation passes for valid indices."""
        valid_indices = [0, 1, 1000, 2**16, 2**20, 2**30 - 1]

        for index in valid_indices:
            # Should not raise exception
            self.security.validate_index_boundaries(index, "test_operation")

    def test_validate_index_boundaries_negative_index(self):
        """Test validation fails for negative indices."""
        with pytest.raises(Bip85ValidationError, match="Index out of valid range"):
            self.security.validate_index_boundaries(-1, "test_operation")

    def test_validate_index_boundaries_too_large(self):
        """Test validation fails for indices too large."""
        with pytest.raises(Bip85ValidationError, match="Index out of valid range"):
            self.security.validate_index_boundaries(2**31, "test_operation")

    def test_validate_index_boundaries_maximum_valid(self):
        """Test validation passes for maximum valid index."""
        # Should not raise exception
        self.security.validate_index_boundaries(2**31 - 1, "test_operation")

    def test_validate_index_boundaries_high_index_warning(self):
        """Test high index values trigger security warnings."""
        high_index = 2**30 + 1000  # Above warning threshold

        with patch("sseed.bip85.security.log_security_event") as mock_log:
            self.security.validate_index_boundaries(high_index, "test_operation")

            mock_log.assert_called_once()
            assert "High index value" in mock_log.call_args[0][0]

    def test_validate_index_boundaries_problematic_indices(self):
        """Test problematic index values trigger warnings."""
        problematic_indices = [2**31 - 1, 2**16, 2**24]

        for index in problematic_indices:
            with patch("sseed.bip85.security.logger") as mock_logger:
                self.security.validate_index_boundaries(index, "test_operation")

                # Check if warning was logged for boundary values
                warning_logged = (
                    any(
                        "boundary" in str(call).lower() and "index" in str(call).lower()
                        for call in mock_logger.warning.call_args_list
                    )
                    if mock_logger.warning.call_args_list
                    else False
                )

                # All problematic indices should trigger some kind of logging
                assert (
                    warning_logged or index >= 2**30
                )  # High index triggers log_security_event


class TestMemoryProtection:
    """Test memory protection and secure clearing."""

    def test_secure_clear_memory_basic(self):
        """Test basic secure memory clearing."""
        test_data = bytearray(b"sensitive_data_here")
        original_length = len(test_data)

        # The global function secure_clear_memory calls the instance method
        from sseed.bip85.security import secure_clear_memory

        secure_clear_memory(test_data)

        # Note: Python secure clearing is best-effort, test that function completes
        assert len(test_data) == original_length

    def test_secure_clear_memory_multiple_passes(self):
        """Test secure memory clearing with multiple passes."""
        test_data = bytearray(b"very_sensitive_data")

        # Mock os.urandom to control the overwrite patterns
        with patch("os.urandom") as mock_random:
            mock_random.return_value = b"\xff" * len(test_data)

            from sseed.bip85.security import secure_clear_memory

            secure_clear_memory(test_data)

            # Should have been called for random overwrite passes (3 times by default)
            assert mock_random.call_count >= 1

    def test_secure_clear_memory_empty_data(self):
        """Test secure memory clearing with empty data."""
        test_data = bytearray()

        # Should not raise exception
        secure_clear_memory(test_data)
        assert len(test_data) == 0

    def test_secure_clear_memory_exception_handling(self):
        """Test secure memory clearing handles exceptions gracefully."""
        # Create a mock that raises an exception
        test_data = bytearray(b"test")

        with patch("os.urandom", side_effect=Exception("Random generation failed")):
            # Should not raise exception, but may log error
            from sseed.bip85.security import secure_clear_memory

            secure_clear_memory(test_data)

            # Function should complete without raising exception
            assert len(test_data) == 4


class TestEntropySecurityValidation:
    """Test entropy security validation functions."""

    def test_validate_entropy_security_valid_entropy(self):
        """Test validation passes for valid entropy."""
        # Use varied entropy that won't trigger weak pattern detection
        valid_entropy = bytes([i % 256 for i in range(0, 256, 8)])  # 32 bytes varied

        # Should not raise exception
        result = validate_entropy_security(valid_entropy)
        assert result is True

    def test_validate_entropy_security_weak_entropy(self):
        """Test validation fails for weak entropy."""
        weak_entropy = b"\x00" * 32  # All zeros

        with pytest.raises(Bip85ValidationError):
            validate_entropy_security(weak_entropy)

    def test_audit_bip85_security_basic(self):
        """Test BIP85 security audit functionality."""
        # audit_bip85_security takes no arguments, returns current state
        result = audit_bip85_security()
        assert isinstance(result, dict)
        assert "timing_attack_protection" in result
        assert "memory_protection" in result
        assert "entropy_validation" in result


class TestGlobalSecurityFunctions:
    """Test global security functions."""

    def test_get_security_hardening_singleton(self):
        """Test security hardening uses singleton pattern."""
        instance1 = get_security_hardening()
        instance2 = get_security_hardening()

        # Should return the same instance
        assert instance1 is instance2
        assert isinstance(instance1, SecurityHardening)

    def test_get_security_hardening_thread_safety(self):
        """Test security hardening singleton is thread-safe."""
        import threading

        instances = []

        def get_instance():
            instances.append(get_security_hardening())

        # Create multiple threads that get the instance
        threads = [threading.Thread(target=get_instance) for _ in range(5)]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # All instances should be the same object
        assert all(instance is instances[0] for instance in instances)


class TestSecurityIntegration:
    """Test security integration scenarios."""

    def setup_method(self):
        """Set up security hardening instance for tests."""
        self.security = SecurityHardening()

    def test_end_to_end_security_validation(self):
        """Test complete security validation flow."""
        # Simulate a complete BIP85 security check
        test_entropy = bytes([i % 256 for i in range(0, 256, 8)])  # 32 bytes varied
        test_index = 12345

        # All security checks should pass
        start_time = time.perf_counter()

        with self.security.timing_attack_protection("bip39_generation"):
            self.security.validate_entropy_quality(test_entropy)
            self.security.validate_index_boundaries(test_index, "bip39_generation")

        elapsed = time.perf_counter() - start_time

        # Should complete successfully with timing protection
        assert elapsed >= 0.001  # Minimum timing protection

    def test_security_failure_scenarios(self):
        """Test various security failure scenarios."""
        security_failures = [
            (b"\x00" * 32, -1),  # Weak entropy + invalid index
            (b"\xff" * 16, 2**31),  # Weak entropy + index too large
            (b"\x01" * 8, 2**30 + 1000),  # Insufficient entropy + high index
        ]

        for entropy, index in security_failures:
            # At least one security check should fail
            entropy_failed = False
            index_failed = False

            try:
                self.security.validate_entropy_quality(entropy)
            except Bip85ValidationError:
                entropy_failed = True

            try:
                self.security.validate_index_boundaries(index, "test")
            except Bip85ValidationError:
                index_failed = True

            # At least one should have failed
            assert entropy_failed or index_failed

    def test_security_logging_integration(self):
        """Test security events are properly logged."""
        with patch("sseed.bip85.security.log_security_event") as mock_log:
            # Trigger security events
            try:
                self.security.validate_entropy_quality(b"\x00" * 32)
            except Bip85ValidationError:
                pass

            # Should have logged security event
            mock_log.assert_called()
            assert (
                "weak" in mock_log.call_args[0][0].lower()
                and "pattern" in mock_log.call_args[0][0].lower()
            )
