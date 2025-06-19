# SSeed Project Makefile
# Provides convenient targets for development and release management

.PHONY: help bump-major bump-minor bump-patch test check install clean docs version ci-test build

# Default target
help: ## Show this help message
	@echo "SSeed Project Management"
	@echo "========================"
	@echo ""
	@echo "Version Management:"
	@echo "  bump-patch     Bump patch version (1.0.1 -> 1.0.2)"
	@echo "  bump-minor     Bump minor version (1.0.1 -> 1.1.0)"
	@echo "  bump-major     Bump major version (1.0.1 -> 2.0.0)"
	@echo "  version        Show current version"
	@echo ""
	@echo "Development:"
	@echo "  test           Run all tests with coverage"
	@echo "  check          Run code quality checks (pylint, flake8, mypy)"
	@echo "  ci-test        Run CI-style tests (lint + mypy + pytest)"
	@echo "  build          Build distribution packages"
	@echo "  install        Install package in development mode"
	@echo "  clean          Clean build artifacts and cache files"
	@echo ""
	@echo "Options for version bumping:"
	@echo "  DRY_RUN=1      Show what would be changed without making changes"
	@echo "  NO_COMMIT=1    Update files but skip git commit and tag"
	@echo "  MESSAGE=\"...\"   Custom commit message"
	@echo ""
	@echo "Examples:"
	@echo "  make bump-patch"
	@echo "  make bump-minor DRY_RUN=1"
	@echo "  make bump-major NO_COMMIT=1"
	@echo "  make bump-patch MESSAGE=\"fix: critical security update\""

# Version management targets
bump-patch: ## Bump patch version (1.0.1 -> 1.0.2)
	@python scripts/bump-version.py patch $(if $(DRY_RUN),--dry-run) $(if $(NO_COMMIT),--no-commit) $(if $(MESSAGE),--message "$(MESSAGE)")

bump-minor: ## Bump minor version (1.0.1 -> 1.1.0)
	@python scripts/bump-version.py minor $(if $(DRY_RUN),--dry-run) $(if $(NO_COMMIT),--no-commit) $(if $(MESSAGE),--message "$(MESSAGE)")

bump-major: ## Bump major version (1.0.1 -> 2.0.0)
	@python scripts/bump-version.py major $(if $(DRY_RUN),--dry-run) $(if $(NO_COMMIT),--no-commit) $(if $(MESSAGE),--message "$(MESSAGE)")

version: ## Show current version
	@python -c "from sseed import __version__; print(f'Current version: {__version__}')"

# Development targets
test: ## Run all tests with coverage
	@echo "🧪 Running tests with coverage..."
	@python -m pytest --cov=sseed --cov-report=html --cov-report=term-missing

check: ## Run code quality checks
	@echo "🔍 Running code quality checks..."
	@echo "Running pylint..."
	@python -m pylint sseed/
	@echo "Running flake8..."
	@python -m flake8 sseed/
	@echo "Running mypy..."
	@python -m mypy sseed/

install: ## Install package in development mode
	@echo "📦 Installing sseed in development mode..."
	@python -m pip install -e .

clean: ## Clean build artifacts and cache files
	@echo "🧹 Cleaning build artifacts..."
	@rm -rf build/
	@rm -rf dist/
	@rm -rf *.egg-info/
	@rm -rf .pytest_cache/
	@rm -rf .coverage
	@rm -rf htmlcov/
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete

# CI/CD targets
ci-test: ## Run CI-style tests (same as GitHub Actions)
	@echo "🧪 Running CI-style tests..."
	@echo "1️⃣ Linting (Pylint)..."
	@python -m pylint sseed/ --fail-under=9.5
	@echo "2️⃣ Type checking (MyPy)..."
	@python -m mypy sseed/
	@echo "3️⃣ Style check (Black)..."
	@python -m black --check sseed/ tests/
	@echo "4️⃣ Running tests with coverage..."
	@python -m pytest --cov=sseed --cov-fail-under=85 --cov-report=term-missing -v tests/
	@echo "✅ All CI checks passed!"

build: ## Build distribution packages
	@echo "📦 Building distribution packages..."
	@python -m pip install --upgrade build twine
	@python -m build
	@python -m twine check dist/*
	@echo "✅ Packages built successfully!"

# Advanced version management (specific versions)
bump-to: ## Bump to specific version (usage: make bump-to VERSION=1.2.3)
	@if [ -z "$(VERSION)" ]; then \
		echo "❌ Error: VERSION is required. Usage: make bump-to VERSION=1.2.3"; \
		exit 1; \
	fi
	@python scripts/bump-version.py $(VERSION) $(if $(DRY_RUN),--dry-run) $(if $(NO_COMMIT),--no-commit) $(if $(MESSAGE),--message "$(MESSAGE)")

# Pre-release versions
bump-alpha: ## Bump to alpha pre-release (usage: make bump-alpha [ALPHA=1])
	@python -c "from sseed import __version__; \
		import re; \
		v = __version__; \
		match = re.match(r'^(\d+)\.(\d+)\.(\d+)', v); \
		if match: \
			major, minor, patch = match.groups(); \
			alpha_num = '$(ALPHA)' if '$(ALPHA)' else '1'; \
			new_version = f'{major}.{minor}.{patch}a{alpha_num}'; \
			print(f'New alpha version: {new_version}'); \
		else: \
			print('❌ Error: Could not parse current version'); \
			exit(1)" | tail -1 | sed 's/New alpha version: //' | xargs -I {} python scripts/bump-version.py {} $(if $(DRY_RUN),--dry-run) $(if $(NO_COMMIT),--no-commit) $(if $(MESSAGE),--message "$(MESSAGE)")

bump-beta: ## Bump to beta pre-release (usage: make bump-beta [BETA=1])
	@python -c "from sseed import __version__; \
		import re; \
		v = __version__; \
		match = re.match(r'^(\d+)\.(\d+)\.(\d+)', v); \
		if match: \
			major, minor, patch = match.groups(); \
			beta_num = '$(BETA)' if '$(BETA)' else '1'; \
			new_version = f'{major}.{minor}.{patch}b{beta_num}'; \
			print(f'New beta version: {new_version}'); \
		else: \
			print('❌ Error: Could not parse current version'); \
			exit(1)" | tail -1 | sed 's/New beta version: //' | xargs -I {} python scripts/bump-version.py {} $(if $(DRY_RUN),--dry-run) $(if $(NO_COMMIT),--no-commit) $(if $(MESSAGE),--message "$(MESSAGE)")

bump-rc: ## Bump to release candidate (usage: make bump-rc [RC=1])
	@python -c "from sseed import __version__; \
		import re; \
		v = __version__; \
		match = re.match(r'^(\d+)\.(\d+)\.(\d+)', v); \
		if match: \
			major, minor, patch = match.groups(); \
			rc_num = '$(RC)' if '$(RC)' else '1'; \
			new_version = f'{major}.{minor}.{patch}rc{rc_num}'; \
			print(f'New RC version: {new_version}'); \
		else: \
			print('❌ Error: Could not parse current version'); \
			exit(1)" | tail -1 | sed 's/New RC version: //' | xargs -I {} python scripts/bump-version.py {} $(if $(DRY_RUN),--dry-run) $(if $(NO_COMMIT),--no-commit) $(if $(MESSAGE),--message "$(MESSAGE)") 