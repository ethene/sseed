"""Tests for the bump-version script functionality.

These tests verify:
- PEP 440 version validation
- Version parsing and bumping logic
- File update operations
- Changelog management
- Git integration
- Error handling
"""

import importlib.util
import subprocess

# Import the BumpVersion class from the script
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

# Import with importlib since the filename has a hyphen
import importlib.util

spec = importlib.util.spec_from_file_location(
    "bump_version", Path(__file__).parent.parent / "scripts" / "bump-version.py"
)
bump_version_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bump_version_module)

BumpVersion = bump_version_module.BumpVersion
VersionError = bump_version_module.VersionError


class TestVersionValidation:
    """Test PEP 440 version validation."""

    def test_valid_pep440_versions(self):
        """Test that valid PEP 440 versions pass validation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            self._create_minimal_project(temp_path)
            bumper = BumpVersion(temp_path)

            valid_versions = [
                "1.0.0",
                "1.2.3",
                "1.0.0a1",
                "1.0.0b2",
                "1.0.0rc1",
                "1.0.0.post1",
                "1.0.0.dev1",
                "2.0.0a1.dev456",
                "12.34.56",
                "1.1.2.post1.dev123",
                "1.0",
                "1",
            ]

            for version in valid_versions:
                assert bumper.validate_pep440(
                    version
                ), f"Version {version} should be valid"

    def test_invalid_pep440_versions(self):
        """Test that invalid PEP 440 versions fail validation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            self._create_minimal_project(temp_path)
            bumper = BumpVersion(temp_path)

            invalid_versions = [
                "v1.0.0",  # 'v' prefix not allowed
                "1.0.0-alpha",  # dash not allowed
                "1.0.0+build",  # local versions have different syntax
                "1.0.0.alpha",  # incorrect pre-release format
                "",  # empty string
                "abc",  # non-numeric
                "1.0.0.0.0.0",  # while technically valid, let's keep it reasonable
            ]

            for version in invalid_versions:
                if version == "1.0.0.0.0.0":
                    # This is actually valid per PEP 440, so skip
                    continue
                assert not bumper.validate_pep440(
                    version
                ), f"Version {version} should be invalid"

    def _create_minimal_project(self, temp_path: Path):
        """Create minimal project structure for testing."""
        # Create sseed/__init__.py
        sseed_dir = temp_path / "sseed"
        sseed_dir.mkdir(exist_ok=True)
        (sseed_dir / "__init__.py").write_text('__version__ = "1.0.0"')

        # Create pyproject.toml
        (temp_path / "pyproject.toml").write_text(
            """
[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "sseed"
version = "1.0.0"
"""
        )


class TestVersionParsing:
    """Test version parsing and bumping logic."""

    def test_parse_version(self):
        """Test version string parsing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            self._create_minimal_project(temp_path)
            bumper = BumpVersion(temp_path)

            test_cases = [
                ("1.2.3", (1, 2, 3)),
                ("10.20.30", (10, 20, 30)),
                ("1.0.0a1", (1, 0, 0)),  # Pre-release suffix ignored
                ("2.1.0rc1", (2, 1, 0)),
            ]

            for version_str, expected in test_cases:
                result = bumper.parse_version(version_str)
                assert result == expected, f"Failed to parse {version_str}"

    def test_parse_invalid_version(self):
        """Test parsing invalid version strings."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            self._create_minimal_project(temp_path)
            bumper = BumpVersion(temp_path)

            invalid_versions = ["invalid", "1.2", "a.b.c"]

            for version in invalid_versions:
                with pytest.raises(VersionError):
                    bumper.parse_version(version)

    def test_bump_version_types(self):
        """Test different version bump types."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            self._create_minimal_project(temp_path)
            bumper = BumpVersion(temp_path)

            test_cases = [
                ("1.2.3", "patch", "1.2.4"),
                ("1.2.3", "minor", "1.3.0"),
                ("1.2.3", "major", "2.0.0"),
                ("0.9.9", "patch", "0.9.10"),
                ("0.9.9", "minor", "0.10.0"),
                ("0.9.9", "major", "1.0.0"),
            ]

            for current, bump_type, expected in test_cases:
                result = bumper.bump_version(current, bump_type)
                assert (
                    result == expected
                ), f"Bumping {current} {bump_type} should give {expected}, got {result}"

    def test_bump_invalid_type(self):
        """Test bumping with invalid bump type."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            self._create_minimal_project(temp_path)
            bumper = BumpVersion(temp_path)

            with pytest.raises(VersionError):
                bumper.bump_version("1.0.0", "invalid")

    def _create_minimal_project(self, temp_path: Path):
        """Create minimal project structure for testing."""
        # Create sseed/__init__.py
        sseed_dir = temp_path / "sseed"
        sseed_dir.mkdir(exist_ok=True)
        (sseed_dir / "__init__.py").write_text('__version__ = "1.0.0"')

        # Create pyproject.toml
        (temp_path / "pyproject.toml").write_text(
            """
[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "sseed"
version = "1.0.0"
"""
        )


class TestFileOperations:
    """Test file update operations."""

    def test_get_current_version(self):
        """Test extracting current version from __init__.py."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Test different __version__ formats
            test_cases = [
                '__version__ = "1.2.3"',
                "__version__ = '1.2.3'",
                '__version__="1.2.3"',
                '  __version__  =  "1.2.3"  ',
            ]

            for init_content in test_cases:
                self._create_project_with_init(temp_path, init_content)
                bumper = BumpVersion(temp_path)

                version = bumper.get_current_version()
                assert (
                    version == "1.2.3"
                ), f"Failed to extract version from: {init_content}"

    def test_get_current_version_missing(self):
        """Test error when __version__ is missing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            self._create_project_with_init(temp_path, "# No version here")
            bumper = BumpVersion(temp_path)

            with pytest.raises(VersionError, match="Could not find __version__"):
                bumper.get_current_version()

    def test_update_init_file_dry_run(self):
        """Test updating __init__.py in dry-run mode."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            original_content = '__version__ = "1.0.0"'
            self._create_project_with_init(temp_path, original_content)
            bumper = BumpVersion(temp_path)

            # Test dry run - should not modify file
            bumper.update_init_file("1.0.1", dry_run=True)

            # File should be unchanged
            actual_content = (temp_path / "sseed" / "__init__.py").read_text()
            assert actual_content == original_content

    def test_update_init_file_real(self):
        """Test actually updating __init__.py."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            self._create_project_with_init(temp_path, '__version__ = "1.0.0"')
            bumper = BumpVersion(temp_path)

            # Test real update
            bumper.update_init_file("1.0.1", dry_run=False)

            # File should be updated
            actual_content = (temp_path / "sseed" / "__init__.py").read_text()
            assert '__version__ = "1.0.1"' in actual_content

    def test_update_pyproject_file(self):
        """Test updating pyproject.toml."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            self._create_minimal_project(temp_path)
            bumper = BumpVersion(temp_path)

            # Test real update
            bumper.update_pyproject_file("1.0.1", dry_run=False)

            # File should be updated
            actual_content = (temp_path / "pyproject.toml").read_text()
            assert 'version = "1.0.1"' in actual_content

    def _create_project_with_init(self, temp_path: Path, init_content: str):
        """Create project with specific __init__.py content."""
        # Create sseed/__init__.py
        sseed_dir = temp_path / "sseed"
        sseed_dir.mkdir(exist_ok=True)
        (sseed_dir / "__init__.py").write_text(init_content)

        # Create pyproject.toml
        (temp_path / "pyproject.toml").write_text(
            """
[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "sseed"
version = "1.0.0"
"""
        )

    def _create_minimal_project(self, temp_path: Path):
        """Create minimal project structure for testing."""
        self._create_project_with_init(temp_path, '__version__ = "1.0.0"')


class TestChangelogManagement:
    """Test changelog update functionality."""

    def test_update_changelog_new_file(self):
        """Test creating new changelog file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            self._create_minimal_project(temp_path)
            bumper = BumpVersion(temp_path)

            # Update changelog (file doesn't exist)
            bumper.update_changelog("1.0.1", dry_run=False)

            # Check that file was created
            changelog_path = temp_path / "CHANGELOG.md"
            assert changelog_path.exists()

            content = changelog_path.read_text()
            assert "## [1.0.1]" in content
            assert "## [Unreleased]" in content

    def test_update_changelog_existing_file(self):
        """Test updating existing changelog file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            self._create_minimal_project(temp_path)

            # Create existing changelog
            changelog_path = temp_path / "CHANGELOG.md"
            changelog_path.write_text(
                """# Changelog

## [Unreleased]

### Added
- New feature

## [1.0.0] - 2024-01-01

### Added
- Initial release
"""
            )

            bumper = BumpVersion(temp_path)
            bumper.update_changelog("1.0.1", dry_run=False)

            content = changelog_path.read_text()
            assert "## [1.0.1]" in content
            assert "## [Unreleased]" in content
            assert "## [1.0.0]" in content

    def test_update_changelog_dry_run(self):
        """Test changelog update in dry-run mode."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            self._create_minimal_project(temp_path)
            bumper = BumpVersion(temp_path)

            # Test dry run
            bumper.update_changelog("1.0.1", dry_run=True)

            # File should not be created
            changelog_path = temp_path / "CHANGELOG.md"
            assert not changelog_path.exists()

    def _create_minimal_project(self, temp_path: Path):
        """Create minimal project structure for testing."""
        # Create sseed/__init__.py
        sseed_dir = temp_path / "sseed"
        sseed_dir.mkdir(exist_ok=True)
        (sseed_dir / "__init__.py").write_text('__version__ = "1.0.0"')

        # Create pyproject.toml
        (temp_path / "pyproject.toml").write_text(
            """
[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "sseed"
version = "1.0.0"
"""
        )


class TestGitIntegration:
    """Test git commit and tag functionality."""

    @patch("subprocess.run")
    def test_git_commit_and_tag_dry_run(self, mock_run):
        """Test git operations in dry-run mode."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            self._create_minimal_project(temp_path)
            bumper = BumpVersion(temp_path)

            # Test dry run
            bumper.git_commit_and_tag("1.0.1", dry_run=True)

            # No git commands should be executed
            mock_run.assert_not_called()

    @patch("subprocess.run")
    def test_git_commit_and_tag_real(self, mock_run):
        """Test actual git operations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            self._create_minimal_project(temp_path)
            bumper = BumpVersion(temp_path)

            # Test real execution
            bumper.git_commit_and_tag("1.0.1", dry_run=False)

            # Check that git commands were called
            assert mock_run.call_count == 3

            # Verify the commands
            calls = mock_run.call_args_list
            assert calls[0][0][0] == ["git", "add", "."]
            assert calls[1][0][0] == [
                "git",
                "commit",
                "-m",
                "chore: bump version to 1.0.1",
            ]
            assert calls[2][0][0] == ["git", "tag", "v1.0.1"]

    @patch("subprocess.run")
    def test_git_commit_custom_message(self, mock_run):
        """Test git commit with custom message."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            self._create_minimal_project(temp_path)
            bumper = BumpVersion(temp_path)

            # Test with custom message
            custom_message = "feat: add new feature"
            bumper.git_commit_and_tag("1.0.1", message=custom_message, dry_run=False)

            # Check commit message
            calls = mock_run.call_args_list
            assert calls[1][0][0] == ["git", "commit", "-m", custom_message]

    @patch("subprocess.run")
    def test_git_failure_handling(self, mock_run):
        """Test handling of git command failures."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            self._create_minimal_project(temp_path)
            bumper = BumpVersion(temp_path)

            # Mock git command failure
            mock_run.side_effect = subprocess.CalledProcessError(1, "git")

            with pytest.raises(VersionError, match="Git operation failed"):
                bumper.git_commit_and_tag("1.0.1", dry_run=False)

    def _create_minimal_project(self, temp_path: Path):
        """Create minimal project structure for testing."""
        # Create sseed/__init__.py
        sseed_dir = temp_path / "sseed"
        sseed_dir.mkdir(exist_ok=True)
        (sseed_dir / "__init__.py").write_text('__version__ = "1.0.0"')

        # Create pyproject.toml
        (temp_path / "pyproject.toml").write_text(
            """
[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "sseed"
version = "1.0.0"
"""
        )


class TestErrorHandling:
    """Test error handling scenarios."""

    def test_missing_init_file(self):
        """Test error when __init__.py is missing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create pyproject.toml but no __init__.py
            (temp_path / "pyproject.toml").write_text(
                """
[project]
name = "sseed"
version = "1.0.0"
"""
            )

            with pytest.raises(VersionError, match="__init__.py not found"):
                BumpVersion(temp_path)

    def test_missing_pyproject_file(self):
        """Test error when pyproject.toml is missing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create sseed/__init__.py but no pyproject.toml
            sseed_dir = temp_path / "sseed"
            sseed_dir.mkdir(exist_ok=True)
            (sseed_dir / "__init__.py").write_text('__version__ = "1.0.0"')

            with pytest.raises(VersionError, match="pyproject.toml not found"):
                BumpVersion(temp_path)

    def test_invalid_bump_type(self):
        """Test error with invalid bump type."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            self._create_minimal_project(temp_path)
            bumper = BumpVersion(temp_path)

            with pytest.raises(VersionError, match="Invalid bump type"):
                bumper.bump_version("1.0.0", "invalid")

    def _create_minimal_project(self, temp_path: Path):
        """Create minimal project structure for testing."""
        # Create sseed/__init__.py
        sseed_dir = temp_path / "sseed"
        sseed_dir.mkdir(exist_ok=True)
        (sseed_dir / "__init__.py").write_text('__version__ = "1.0.0"')

        # Create pyproject.toml
        (temp_path / "pyproject.toml").write_text(
            """
[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "sseed"
version = "1.0.0"
"""
        )


class TestIntegration:
    """Integration tests for the complete workflow."""

    @patch("subprocess.run")
    def test_full_patch_bump_workflow(self, mock_run):
        """Test complete patch version bump workflow."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            self._create_complete_project(temp_path)
            bumper = BumpVersion(temp_path)

            # Run complete workflow
            bumper.run("patch", dry_run=False, no_commit=False)

            # Verify version updates
            init_content = (temp_path / "sseed" / "__init__.py").read_text()
            assert '__version__ = "1.0.1"' in init_content

            pyproject_content = (temp_path / "pyproject.toml").read_text()
            assert 'version = "1.0.1"' in pyproject_content

            # Verify changelog
            changelog_content = (temp_path / "CHANGELOG.md").read_text()
            assert "## [1.0.1]" in changelog_content

            # Verify git commands were called
            assert mock_run.call_count == 3

    @patch("subprocess.run")
    def test_no_commit_workflow(self, mock_run):
        """Test workflow with --no-commit flag."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            self._create_complete_project(temp_path)
            bumper = BumpVersion(temp_path)

            # Run with no_commit=True
            bumper.run("patch", dry_run=False, no_commit=True)

            # Files should be updated
            init_content = (temp_path / "sseed" / "__init__.py").read_text()
            assert '__version__ = "1.0.1"' in init_content

            # But no git commands should be executed
            mock_run.assert_not_called()

    def test_dry_run_workflow(self):
        """Test complete dry-run workflow."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            self._create_complete_project(temp_path)
            bumper = BumpVersion(temp_path)

            # Store original content
            original_init = (temp_path / "sseed" / "__init__.py").read_text()
            original_pyproject = (temp_path / "pyproject.toml").read_text()

            # Run dry run
            bumper.run("patch", dry_run=True, no_commit=False)

            # Files should be unchanged
            assert (temp_path / "sseed" / "__init__.py").read_text() == original_init
            assert (temp_path / "pyproject.toml").read_text() == original_pyproject
            assert not (temp_path / "CHANGELOG.md").exists()

    def _create_complete_project(self, temp_path: Path):
        """Create complete project structure for testing."""
        # Create sseed/__init__.py
        sseed_dir = temp_path / "sseed"
        sseed_dir.mkdir(exist_ok=True)
        (sseed_dir / "__init__.py").write_text('__version__ = "1.0.0"')

        # Create pyproject.toml
        (temp_path / "pyproject.toml").write_text(
            """
[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "sseed"
version = "1.0.0"
"""
        )


if __name__ == "__main__":
    pytest.main([__file__])
