"""Tests to fill coverage gaps in sseed.validation.structure module."""

import logging
from unittest.mock import patch

import pytest

from sseed.exceptions import ValidationError
from sseed.validation.structure import validate_group_threshold


class TestValidationStructureGaps:
    """Test specific gaps in validation structure module."""

    def test_validate_group_threshold_zero_total_shares(self):
        """Test ValidationError for zero total shares."""
        # This should trigger line 73 - total_shares <= 0
        with pytest.raises(ValidationError, match="Total shares must be positive"):
            validate_group_threshold("2-of-0")  # Zero total shares

    def test_validate_group_threshold_zero_threshold(self):
        """Test ValidationError for zero threshold."""
        # This should trigger line 67 - threshold <= 0
        with pytest.raises(ValidationError, match="Threshold must be positive"):
            validate_group_threshold("0-of-5")  # Zero threshold

    def test_validate_group_threshold_threshold_one_warning(self):
        """Test warning log for threshold of 1 with multiple shares."""
        # This should trigger line 93 - warning for threshold=1 with multiple shares
        # Use mock to capture the warning call directly
        with patch("sseed.validation.structure.logger.warning") as mock_warning:
            threshold, total = validate_group_threshold("1-of-5")

        assert threshold == 1
        assert total == 5

        # Verify the warning was called with the expected message
        mock_warning.assert_called_once_with(
            "Threshold of 1 provides no security benefit with multiple shares"
        )

    def test_validate_group_threshold_additional_edge_cases(self):
        """Test additional edge cases for complete coverage."""
        # Test valid cases to ensure no regressions
        threshold, total = validate_group_threshold("3-of-5")
        assert threshold == 3
        assert total == 5

        # Test edge case: threshold equals total
        threshold, total = validate_group_threshold("5-of-5")
        assert threshold == 5
        assert total == 5
