# Version Management System

## Overview

SSeed implements a comprehensive version management system that ensures PEP 440 compliance, automatic changelog updates, and seamless Git integration. The system prevents non-compliant version tags and automates the entire release workflow.

## Features

### 🔒 **PEP 440 Compliance**
- **Strict Validation**: All version strings validated against PEP 440 specification
- **Format Support**: Supports standard formats (1.2.3), pre-releases (1.2.3a1, 1.2.3b2, 1.2.3rc1), post-releases (1.2.3.post1), and development releases (1.2.3.dev1)
- **Error Prevention**: Blocks invalid formats like "v1.2.3", "1.2.3-alpha", etc.

### 📝 **Automatic Changelog Management**
- **Keep a Changelog Format**: Follows industry standard changelog format
- **Version Entries**: Automatically creates new version sections with timestamps
- **Unreleased Section**: Maintains unreleased changes section for ongoing development
- **Git Links**: Updates comparison links for version diffs

### 🔄 **Multi-File Synchronization**
- **Version Consistency**: Updates version in `__init__.py` and `pyproject.toml` simultaneously
- **Single Source of Truth**: Prevents version drift between files
- **Validation**: Ensures all files are properly updated before proceeding

### 🔧 **Git Integration**
- **Automatic Commits**: Creates commit with conventional commit message format
- **Tag Creation**: Creates properly formatted Git tags (v1.2.3)
- **Push Instructions**: Provides clear next steps for publishing

### 🧪 **Dry-Run Support**
- **Safe Testing**: Preview all changes without making modifications
- **File Updates**: Shows exactly what would be changed
- **Git Commands**: Displays git commands that would be executed

## Usage Examples

### Basic Version Bumping
```bash
# Bump patch version (1.0.1 → 1.0.2)
make bump-patch

# Bump minor version (1.0.1 → 1.1.0)
make bump-minor

# Bump major version (1.0.1 → 2.0.0)
make bump-major

# Set specific version
make bump-to VERSION=1.2.3
```

### Advanced Options
```bash
# Preview changes without making them
make bump-patch DRY_RUN=1

# Update files but skip git commit/tag
make bump-minor NO_COMMIT=1

# Custom commit message
make bump-patch MESSAGE="fix: critical security update"
```

### Pre-Release Versions
```bash
# Create alpha release (1.0.1 → 1.0.1a1)
make bump-alpha

# Create beta release (1.0.1 → 1.0.1b1)
make bump-beta BETA=2  # Custom beta number

# Create release candidate (1.0.1 → 1.0.1rc1)
make bump-rc RC=3  # Custom RC number
```

### Direct Script Usage
```bash
# Basic usage
python scripts/bump-version.py patch
python scripts/bump-version.py minor
python scripts/bump-version.py major

# Specific version
python scripts/bump-version.py 1.2.3

# With options
python scripts/bump-version.py patch --dry-run
python scripts/bump-version.py minor --no-commit
python scripts/bump-version.py patch --message "fix: resolve security issue"
```

## Script Architecture

### Core Components

#### **BumpVersion Class**
- **Project Detection**: Automatically finds project root
- **Version Extraction**: Reads current version from `__init__.py`
- **PEP 440 Validation**: Comprehensive version format checking
- **File Operations**: Safe file updates with error handling

#### **Version Parsing Engine**
- **Semantic Parsing**: Extracts major, minor, patch components
- **Pre-release Handling**: Supports alpha, beta, RC versions
- **Increment Logic**: Smart version bumping based on type

#### **Changelog Manager**
- **Format Detection**: Recognizes Keep a Changelog format
- **Section Creation**: Adds new version sections with dates
- **Link Updates**: Maintains Git comparison links
- **Backup Safety**: Preserves existing content

#### **Git Integration**
- **Command Execution**: Runs git add, commit, and tag
- **Error Handling**: Graceful failure recovery
- **Status Reporting**: Clear success/failure feedback

### Validation Pipeline

```
1. Project Structure Validation
   ├── Check __init__.py exists
   ├── Check pyproject.toml exists
   └── Validate project layout

2. Version Processing
   ├── Extract current version
   ├── Calculate new version
   └── Validate PEP 440 compliance

3. File Updates
   ├── Update __init__.py
   ├── Update pyproject.toml
   └── Update CHANGELOG.md

4. Git Operations
   ├── Stage changes (git add)
   ├── Create commit with message
   └── Create version tag
```

## Error Handling

### Version Validation Errors
```bash
❌ Error: Version 'v1.2.3' is not PEP 440 compliant.
Use formats like: 1.2.3, 1.2.3a1, 1.2.3b2, 1.2.3rc1, 1.2.3.post1, 1.2.3.dev1
```

### File System Errors
```bash
❌ Error: __init__.py not found: /path/to/sseed/__init__.py
❌ Error: Could not find __version__ in __init__.py
```

### Git Operation Errors
```bash
❌ Error: Git operation failed: Command 'git commit' returned non-zero exit status 1
```

### Recovery Strategies
- **Dry-run first**: Always test with `--dry-run` before real execution
- **No-commit option**: Use `--no-commit` to update files without Git operations
- **Manual recovery**: Clear instructions for fixing failed operations

## Configuration

### Changelog Template
The system uses this changelog structure:
```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- New features

### Changed
- Changes in existing functionality

### Fixed
- Bug fixes

## [1.0.1] - 2024-06-19

### Added
- Initial release features
```

### Git Commit Format
Default commit messages follow conventional commits:
```
chore: bump version to 1.2.3
```

Custom messages can be provided:
```
feat: add new authentication system
fix: resolve memory leak in crypto operations
docs: update API documentation
```

## Integration with Development Workflow

### CI/CD Pipeline Integration
```yaml
# Example GitHub Actions workflow
- name: Bump Version
  run: |
    make bump-patch
    git push && git push --tags

- name: Create Release
  uses: actions/create-release@v1
  with:
    tag_name: ${{ github.ref }}
    release_name: Release ${{ github.ref }}
```

### Pre-commit Hooks
```bash
# Add to .pre-commit-config.yaml
- repo: local
  hooks:
    - id: version-check
      name: Check version consistency
      entry: python scripts/bump-version.py --check
      language: system
```

### Release Automation
```bash
# Complete release workflow
make bump-minor MESSAGE="feat: add new CLI features"
git push && git push --tags
python -m build
python -m twine upload dist/*
```

## Testing

### Test Coverage
- **24 comprehensive tests** covering all functionality
- **PEP 440 validation** with valid/invalid version testing
- **File operations** with different content formats
- **Git integration** with mocked subprocess calls
- **Error scenarios** with proper exception handling
- **Integration workflows** testing complete processes

### Test Categories
1. **Version Validation Tests**: PEP 440 compliance checking
2. **Version Parsing Tests**: Semantic version component extraction
3. **File Operation Tests**: Safe file read/write operations
4. **Changelog Management Tests**: Proper changelog formatting
5. **Git Integration Tests**: Command execution and error handling
6. **Error Handling Tests**: Graceful failure scenarios
7. **Integration Tests**: Complete workflow validation

### Running Tests
```bash
# Run all version management tests
python -m pytest tests/test_bump_version.py -v

# Run with coverage
python -m pytest tests/test_bump_version.py --cov=scripts.bump_version

# Test specific functionality
python -m pytest tests/test_bump_version.py::TestVersionValidation -v
```

## Benefits

### 🛡️ **Reliability**
- **Validation Safety**: Prevents invalid version tags from entering the system
- **Atomic Operations**: All-or-nothing updates prevent partial state corruption
- **Error Recovery**: Clear error messages with recovery instructions

### 🚀 **Developer Experience**
- **Simple Commands**: One-command version bumping with `make bump-patch`
- **Preview Mode**: Dry-run capability for safe testing
- **Flexible Options**: Support for custom messages and no-commit workflows

### 📋 **Compliance**
- **PEP 440 Standards**: Full compliance with Python packaging standards
- **Changelog Standards**: Follows Keep a Changelog best practices
- **Git Standards**: Conventional commit message format

### 🔄 **Automation**
- **Multi-file Sync**: Updates all version references simultaneously
- **Git Integration**: Automatic commit and tag creation
- **CI/CD Ready**: Designed for automated release pipelines

## Implementation Details

### PEP 440 Regex Pattern
```python
pep440_pattern = re.compile(
    r"^([1-9][0-9]*!)?"                # epoch
    r"(0|[1-9][0-9]*)"                 # major
    r"(\.(0|[1-9][0-9]*))*"            # minor, patch, etc.
    r"((a|b|rc)(0|[1-9][0-9]*))?"      # pre-release
    r"(\.post(0|[1-9][0-9]*))?"        # post-release
    r"(\.dev(0|[1-9][0-9]*))?"         # development
    r"$", re.IGNORECASE
)
```

### File Update Strategy
1. **Read current content** into memory
2. **Apply regex substitution** for version strings
3. **Validate changes** before writing
4. **Atomic write** to prevent corruption
5. **Verify updates** by re-reading files

### Changelog Update Algorithm
1. **Detect existing format** or create new structure
2. **Insert new version section** after [Unreleased]
3. **Update comparison links** at file bottom
4. **Preserve all existing content** and formatting

This version management system provides enterprise-grade reliability while maintaining developer-friendly simplicity, ensuring that all releases follow proper versioning standards and include comprehensive change documentation. 