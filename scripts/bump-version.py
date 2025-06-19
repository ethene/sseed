#!/usr/bin/env python3
"""
SSeed Version Bumping Script

Automates version management with PEP 440 compliance and changelog generation.

Features:
- PEP 440 version validation
- Automatic file updates (__init__.py, pyproject.toml)
- Changelog management (CHANGELOG.md)
- Git commit and tag creation
- Dry-run mode for testing

Usage:
    python scripts/bump-version.py major|minor|patch [--dry-run] [--no-commit] [--message "Custom message"]
    python scripts/bump-version.py 1.2.3 [--dry-run] [--no-commit]

Examples:
    python scripts/bump-version.py patch              # 1.0.1 -> 1.0.2
    python scripts/bump-version.py minor              # 1.0.1 -> 1.1.0
    python scripts/bump-version.py major              # 1.0.1 -> 2.0.0
    python scripts/bump-version.py 1.2.3              # Set specific version
    python scripts/bump-version.py patch --dry-run    # Test without changes
"""

import argparse
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple


class VersionError(Exception):
    """Custom exception for version-related errors."""
    pass


class BumpVersion:
    """Version bumping and project management utilities."""
    
    def __init__(self, project_root: Path):
        """Initialize with project root directory."""
        self.project_root = project_root
        self.init_file = project_root / "sseed" / "__init__.py"
        self.pyproject_file = project_root / "pyproject.toml"
        self.changelog_file = project_root / "CHANGELOG.md"
        
        # Validate required files exist
        if not self.init_file.exists():
            raise VersionError(f"__init__.py not found: {self.init_file}")
        if not self.pyproject_file.exists():
            raise VersionError(f"pyproject.toml not found: {self.pyproject_file}")
    
    def get_current_version(self) -> str:
        """Extract current version from __init__.py."""
        content = self.init_file.read_text()
        match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
        if not match:
            raise VersionError("Could not find __version__ in __init__.py")
        return match.group(1)
    
    def validate_pep440(self, version: str) -> bool:
        """Validate version string against PEP 440 specification.
        
        PEP 440 allows:
        - Major.minor.patch (e.g., 1.2.3)
        - Pre-releases (e.g., 1.2.3a1, 1.2.3b2, 1.2.3rc1)
        - Post-releases (e.g., 1.2.3.post1)
        - Development releases (e.g., 1.2.3.dev1)
        """
        # PEP 440 regex pattern
        pep440_pattern = re.compile(
            r"^([1-9][0-9]*!)?"                # epoch
            r"(0|[1-9][0-9]*)"                 # major
            r"(\.(0|[1-9][0-9]*))*"            # minor, patch, etc.
            r"((a|b|rc)(0|[1-9][0-9]*))?"      # pre-release
            r"(\.post(0|[1-9][0-9]*))?"        # post-release
            r"(\.dev(0|[1-9][0-9]*))?"         # development
            r"$", re.IGNORECASE
        )
        
        return bool(pep440_pattern.match(version))
    
    def parse_version(self, version: str) -> Tuple[int, int, int]:
        """Parse version string into major, minor, patch components."""
        # Extract base version (before any pre/post/dev suffixes)
        base_match = re.match(r"^(\d+)\.(\d+)\.(\d+)", version)
        if not base_match:
            raise VersionError(f"Invalid version format: {version}")
        
        return (
            int(base_match.group(1)),
            int(base_match.group(2)),
            int(base_match.group(3))
        )
    
    def bump_version(self, current: str, bump_type: str) -> str:
        """Bump version based on type (major, minor, patch)."""
        major, minor, patch = self.parse_version(current)
        
        if bump_type == "major":
            return f"{major + 1}.0.0"
        elif bump_type == "minor":
            return f"{major}.{minor + 1}.0"
        elif bump_type == "patch":
            return f"{major}.{minor}.{patch + 1}"
        else:
            raise VersionError(f"Invalid bump type: {bump_type}")
    
    def update_init_file(self, new_version: str, dry_run: bool = False) -> None:
        """Update version in __init__.py."""
        content = self.init_file.read_text()
        new_content = re.sub(
            r'(__version__\s*=\s*["\'])[^"\']+(["\'])',
            rf'\g<1>{new_version}\g<2>',
            content
        )
        
        if dry_run:
            print(f"[DRY RUN] Would update {self.init_file}")
            print(f"[DRY RUN] __version__ = \"{new_version}\"")
        else:
            self.init_file.write_text(new_content)
            print(f"✅ Updated {self.init_file}")
    
    def update_pyproject_file(self, new_version: str, dry_run: bool = False) -> None:
        """Update version in pyproject.toml."""
        content = self.pyproject_file.read_text()
        new_content = re.sub(
            r'(version\s*=\s*["\'])[^"\']+(["\'])',
            rf'\g<1>{new_version}\g<2>',
            content
        )
        
        if dry_run:
            print(f"[DRY RUN] Would update {self.pyproject_file}")
            print(f"[DRY RUN] version = \"{new_version}\"")
        else:
            self.pyproject_file.write_text(new_content)
            print(f"✅ Updated {self.pyproject_file}")
    
    def update_changelog(self, new_version: str, dry_run: bool = False) -> None:
        """Update CHANGELOG.md with new version entry."""
        if not self.changelog_file.exists():
            if dry_run:
                print(f"[DRY RUN] Would create {self.changelog_file}")
                return
            else:
                # Create basic changelog structure
                self.changelog_file.write_text(
                    "# Changelog\n\n"
                    "All notable changes to this project will be documented in this file.\n\n"
                    "## [Unreleased]\n\n"
                )
        
        content = self.changelog_file.read_text()
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        # Replace [Unreleased] with new version
        new_content = content.replace(
            "## [Unreleased]",
            f"## [Unreleased]\n\n## [{new_version}] - {current_date}"
        )
        
        # Update comparison links at bottom
        if "[Unreleased]:" in new_content:
            # Update existing links
            new_content = re.sub(
                r"(\[Unreleased\]: https://github\.com/[^/]+/[^/]+/compare/v)[^.]+(\.\.\.[^/]+)(.*)(\n\[[^\]]+\]:.*)?$",
                rf"\g<1>{new_version}\g<2>\g<3>\n[{new_version}]: https://github.com/yourusername/sseed/releases/tag/v{new_version}",
                new_content,
                flags=re.MULTILINE
            )
        else:
            # Add links section
            new_content += f"\n\n[Unreleased]: https://github.com/yourusername/sseed/compare/v{new_version}...HEAD\n"
            new_content += f"[{new_version}]: https://github.com/yourusername/sseed/releases/tag/v{new_version}"
        
        if dry_run:
            print(f"[DRY RUN] Would update {self.changelog_file}")
            print(f"[DRY RUN] Add section: [{new_version}] - {current_date}")
        else:
            self.changelog_file.write_text(new_content)
            print(f"✅ Updated {self.changelog_file}")
    
    def git_commit_and_tag(self, version: str, message: Optional[str] = None, dry_run: bool = False) -> None:
        """Create git commit and tag for the new version."""
        if not message:
            message = f"chore: bump version to {version}"
        
        tag_name = f"v{version}"
        
        if dry_run:
            print(f"[DRY RUN] Would run: git add .")
            print(f"[DRY RUN] Would run: git commit -m \"{message}\"")
            print(f"[DRY RUN] Would run: git tag {tag_name}")
            return
        
        try:
            # Add files
            subprocess.run(["git", "add", "."], check=True, cwd=self.project_root)
            
            # Commit
            subprocess.run(
                ["git", "commit", "-m", message],
                check=True,
                cwd=self.project_root
            )
            
            # Tag
            subprocess.run(
                ["git", "tag", tag_name],
                check=True,
                cwd=self.project_root
            )
            
            print(f"✅ Created git commit and tag: {tag_name}")
            print(f"💡 To push: git push && git push --tags")
            
        except subprocess.CalledProcessError as e:
            raise VersionError(f"Git operation failed: {e}")
    
    def run(self, version_spec: str, dry_run: bool = False, no_commit: bool = False, message: Optional[str] = None) -> None:
        """Main execution function."""
        print(f"🔍 SSeed Version Bumping Script")
        print(f"Project root: {self.project_root}")
        
        # Get current version
        current_version = self.get_current_version()
        print(f"📋 Current version: {current_version}")
        
        # Determine new version
        if version_spec in ["major", "minor", "patch"]:
            new_version = self.bump_version(current_version, version_spec)
            print(f"🔼 Bumping {version_spec}: {current_version} -> {new_version}")
        else:
            new_version = version_spec
            print(f"🎯 Setting specific version: {current_version} -> {new_version}")
        
        # Validate PEP 440 compliance
        if not self.validate_pep440(new_version):
            raise VersionError(
                f"Version '{new_version}' is not PEP 440 compliant. "
                "Use formats like: 1.2.3, 1.2.3a1, 1.2.3b2, 1.2.3rc1, 1.2.3.post1, 1.2.3.dev1"
            )
        
        print(f"✅ Version '{new_version}' is PEP 440 compliant")
        
        if dry_run:
            print("\n🧪 DRY RUN MODE - No changes will be made\n")
        
        # Update files
        self.update_init_file(new_version, dry_run)
        self.update_pyproject_file(new_version, dry_run)
        self.update_changelog(new_version, dry_run)
        
        # Git operations
        if not no_commit:
            self.git_commit_and_tag(new_version, message, dry_run)
        else:
            print("⏭️  Skipping git commit and tag (--no-commit)")
        
        if not dry_run:
            print(f"\n🎉 Successfully bumped version to {new_version}")
        else:
            print(f"\n🧪 Dry run completed - version would be bumped to {new_version}")


def main():
    """Command-line interface."""
    parser = argparse.ArgumentParser(
        description="Bump version with PEP 440 compliance and changelog management",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/bump-version.py patch              # 1.0.1 -> 1.0.2
  python scripts/bump-version.py minor              # 1.0.1 -> 1.1.0
  python scripts/bump-version.py major              # 1.0.1 -> 2.0.0
  python scripts/bump-version.py 1.2.3              # Set specific version
  python scripts/bump-version.py patch --dry-run    # Test without changes
  python scripts/bump-version.py minor --message "feat: new feature"
        """
    )
    
    parser.add_argument(
        "version",
        help="Version bump type (major/minor/patch) or specific version (e.g., 1.2.3)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without making changes"
    )
    parser.add_argument(
        "--no-commit",
        action="store_true",
        help="Update files but skip git commit and tag"
    )
    parser.add_argument(
        "--message",
        help="Custom commit message (default: 'chore: bump version to X.Y.Z')"
    )
    
    args = parser.parse_args()
    
    # Find project root (directory containing pyproject.toml)
    current_dir = Path.cwd()
    project_root = current_dir
    
    # Search up the directory tree for pyproject.toml
    while project_root != project_root.parent:
        if (project_root / "pyproject.toml").exists():
            break
        project_root = project_root.parent
    else:
        print("❌ Error: Could not find pyproject.toml in current directory or parents")
        sys.exit(1)
    
    try:
        bumper = BumpVersion(project_root)
        bumper.run(
            version_spec=args.version,
            dry_run=args.dry_run,
            no_commit=args.no_commit,
            message=args.message
        )
    except VersionError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n⏹️  Operation cancelled by user")
        sys.exit(1)


if __name__ == "__main__":
    main() 