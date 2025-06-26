"""
Basic test coverage for sseed.bip85.security module.

This module provides basic tests for security functionality without
complex entropy validation that may be flaky.
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


class TestSecurityHardeningBasic:
    """Test basic SecurityHardening functionality."""

    @pytest.fixture
    def security(self):
        """Create a SecurityHardening instance for testing."""
        return SecurityHardening()

    def test_init(self, security):
        """Test SecurityHardening initialization."""
        assert security._timing_attack_protection is True
        assert security._memory_protection is True
        assert security._entropy_validation is True

    def test_timing_attack_protection_disabled(self):
        """Test timing attack protection when disabled."""
        security = SecurityHardening()
        security._timing_attack_protection = False

        start_time = time.perf_counter()

        with security.timing_attack_protection("test_operation"):
            pass

        elapsed = time.perf_counter() - start_time

        # Should be very fast when protection is disabled
        assert elapsed < 0.01  # 10ms tolerance

    def test_timing_attack_protection_enabled(self, security):
        """Test timing attack protection when enabled."""
        start_time = time.perf_counter()

        with security.timing_attack_protection("bip39_generation"):
            # Simulate very fast operation
            pass

        elapsed = time.perf_counter() - start_time

        # Should take at least minimum time (1ms for bip39_generation)
        assert elapsed >= 0.001

    def test_validate_index_boundaries_valid(self, security):
        """Test index boundary validation with valid indices."""
        valid_indices = [0, 1, 100, 1000, 2**30 - 1]

        for index in valid_indices:
            # Should not raise exception
            security.validate_index_boundaries(index, "test_operation")

    def test_validate_index_boundaries_invalid_negative(self, security):
        """Test index boundary validation with negative index."""
        with pytest.raises(Bip85ValidationError) as exc_info:
            security.validate_index_boundaries(-1, "test_operation")

        assert "Index out of valid range" in str(exc_info.value)
        assert exc_info.value.parameter == "index"

    def test_validate_index_boundaries_invalid_too_large(self, security):
        """Test index boundary validation with too large index."""
        with pytest.raises(Bip85ValidationError) as exc_info:
            security.validate_index_boundaries(2**31, "test_operation")

        assert "Index out of valid range" in str(exc_info.value)

    def test_validate_master_seed_entropy_invalid_length(self, security):
        """Test master seed entropy validation with invalid length."""
        short_seed = b"\x12\x34\x56\x78"  # Only 4 bytes

        with pytest.raises(Bip85ValidationError) as exc_info:
            security.validate_master_seed_entropy(short_seed)

        assert "Master seed must be 64 bytes" in str(exc_info.value)

    def test_secure_memory_clear(self, security):
        """Test secure memory clearing."""
        test_data = b"sensitive_data_12345"

        # This should not raise an exception
        security.secure_memory_clear(test_data)

    def test_secure_memory_clear_disabled(self):
        """Test secure memory clearing when disabled."""
        security = SecurityHardening()
        security._memory_protection = False

        test_data = b"sensitive_data_12345"

        # Should return immediately when disabled
        security.secure_memory_clear(test_data)

    def test_validate_concurrent_access(self, security):
        """Test concurrent access validation."""
        result = security.validate_concurrent_access("test_operation_123")
        assert isinstance(result, bool)
        assert result is True  # Basic implementation returns True

    def test_detect_side_channel_attacks(self, security):
        """Test side channel attack detection."""
        operation_context = {
            "operation": "bip39_generation",
            "start_time": time.time(),
            "memory_usage": 1024,
        }

        result = security.detect_side_channel_attacks(operation_context)
        assert isinstance(result, bool)

    def test_generate_secure_test_vectors(self, security):
        """Test secure test vector generation."""
        vectors = security.generate_secure_test_vectors(count=3)

        assert len(vectors) == 3
        for seed, metadata in vectors:
            assert isinstance(seed, bytes)
            assert len(seed) == 64  # Master seed length
            assert isinstance(metadata, dict)
            assert "index" in metadata
            assert "length" in metadata  # Not word_count, but length
            assert "application" in metadata

    def test_audit_security_state(self, security):
        """Test security state audit."""
        audit = security.audit_security_state()

        assert isinstance(audit, dict)
        assert "timing_attack_protection" in audit  # Not timestamp
        assert "memory_protection" in audit
        assert "entropy_validation" in audit
        assert "security_features" in audit
        assert "configuration" in audit
        assert audit["timing_attack_protection"] is True
        assert audit["memory_protection"] is True
        assert audit["entropy_validation"] is True


class TestModuleFunctions:
    """Test module-level functions."""

    def test_get_security_hardening(self):
        """Test security hardening singleton getter."""
        hardening1 = get_security_hardening()
        hardening2 = get_security_hardening()

        assert isinstance(hardening1, SecurityHardening)
        assert hardening1 is hardening2  # Should be same instance

    @patch("sseed.bip85.security.get_security_hardening")
    def test_validate_entropy_security(self, mock_get_security):
        """Test module-level entropy validation function."""
        # Mock the security hardening instance
        mock_security = MagicMock()
        mock_security.validate_entropy_quality.return_value = True
        mock_get_security.return_value = mock_security

        # Test the function
        entropy = b"\x12\x34\x56\x78" * 8  # 32 bytes
        result = validate_entropy_security(entropy, min_bits=128)

        assert result is True
        mock_security.validate_entropy_quality.assert_called_once_with(entropy, 128)

    def test_secure_clear_memory(self):
        """Test module-level secure memory clear function."""
        test_data = b"sensitive_data"

        # Should not raise exception
        secure_clear_memory(test_data)

    def test_audit_bip85_security(self):
        """Test module-level security audit function."""
        audit = audit_bip85_security()

        assert isinstance(audit, dict)
        assert "timing_attack_protection" in audit  # Not timestamp
        assert "memory_protection" in audit
        assert "entropy_validation" in audit
        assert "security_features" in audit
        assert "configuration" in audit
        assert audit["timing_attack_protection"] is True
        assert audit["memory_protection"] is True
        assert audit["entropy_validation"] is True
