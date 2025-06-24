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
	@echo "Release Management:"
	@echo "  release        Create GitHub release (automatic via workflow)"
	@echo "  release-manual Create GitHub release manually (requires gh CLI)"
	@echo "  build          Build distribution packages"
	@echo ""
	@echo "Development:"
	@echo "  test           Run all tests with coverage"
	@echo "  check          Run code quality checks (pylint, flake8, mypy)"
	@echo "  format         Auto-format code (Black + isort)"
	@echo "  ci-test        Run CI-style tests (format, lint, security, tests)"
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
	@python -m flake8 --max-line-length=210 --extend-ignore=E203,W503,F401,F841,E402,F811,F541,W293 sseed/ tests/ --statistics
	@echo "Running mypy..."
	@python -m mypy sseed/

format: ## Auto-format code (Black + isort)
	@echo "🎨 Auto-formatting code..."
	@echo "Running Black..."
	@python -m black --line-length 88 sseed/ tests/
	@echo "Running isort..."
	@python -m isort --profile black --line-length 88 --force-grid-wrap 2 sseed/ tests/
	@echo "✅ Code formatted!"

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
	@echo "1️⃣ Code formatting check (Black)..."
	@python -m black --check --diff --line-length 88 sseed/ tests/
	@echo "2️⃣ Import sorting check (isort)..."
	@python -m isort --check-only --diff --profile black --line-length 88 --force-grid-wrap 2 sseed/ tests/
	@echo "3️⃣ Linting (Pylint)..."
	@python -m pylint sseed/ --fail-under=9.4
	@echo "4️⃣ Style check (flake8)..."
	@python -m flake8 --max-line-length=210 --extend-ignore=E203,W503,F401,F841,E402,F811,F541,W293 sseed/ tests/ --statistics
	@echo "5️⃣ Type checking (MyPy)..."
	@python -m mypy sseed/
	@echo "6️⃣ Security analysis (Bandit)..."
	@python -m bandit -r sseed/ -f txt --configfile pyproject.toml
	@echo "7️⃣ Running tests with coverage..."
	@python -m pytest --cov=sseed --cov-fail-under=85 --cov-report=term-missing -v tests/
	@echo "✅ All CI checks passed!"

build: ## Build distribution packages
	@echo "📦 Building distribution packages..."
	@python -m pip install --upgrade build twine
	@python -m build
	@python -m twine check dist/*
	@echo "✅ Packages built successfully!"

release: ## Create GitHub release for current version (requires git push first)
	@echo "🚀 Creating GitHub Release..."
	@CURRENT_VERSION=$$(python -c "from sseed import __version__; print(__version__)"); \
	echo "📋 Current version: $$CURRENT_VERSION"; \
	echo "🏷️  Creating release for v$$CURRENT_VERSION"; \
	if git rev-parse "v$$CURRENT_VERSION" >/dev/null 2>&1; then \
		echo "✅ Tag v$$CURRENT_VERSION exists"; \
		echo "🔄 Pushing tag to trigger release workflow..."; \
		git push origin "v$$CURRENT_VERSION"; \
		echo "✅ GitHub Release workflow triggered!"; \
		echo "🔗 Check status: https://github.com/$$(git config --get remote.origin.url | sed 's/.*github.com[:/]\([^.]*\).*/\1/')/actions"; \
	else \
		echo "❌ Error: Tag v$$CURRENT_VERSION not found"; \
		echo "💡 Run 'make bump-patch' (or bump-minor/major) first to create the tag"; \
		exit 1; \
	fi

release-manual: ## Manually create GitHub release using gh CLI (requires gh CLI)
	@echo "🚀 Creating GitHub Release manually..."
	@CURRENT_VERSION=$$(python -c "from sseed import __version__; print(__version__)"); \
	echo "📋 Current version: $$CURRENT_VERSION"; \
	if git rev-parse "v$$CURRENT_VERSION" >/dev/null 2>&1; then \
		echo "🔨 Building packages..."; \
		make build; \
		echo "📝 Extracting changelog entry..."; \
		awk -v version="$$CURRENT_VERSION" '/^## \[/ { if (found && $$0 !~ "\\[" version "\\]") exit; if ($$0 ~ "\\[" version "\\]") { found=1; next } } found && !/^## \[/ { print }' CHANGELOG.md > /tmp/release_notes.md; \
		echo "🚀 Creating GitHub release..."; \
		gh release create "v$$CURRENT_VERSION" \
			--title "Release $$CURRENT_VERSION" \
			--notes-file /tmp/release_notes.md \
			dist/sseed-$$CURRENT_VERSION-py3-none-any.whl \
			dist/sseed-$$CURRENT_VERSION.tar.gz; \
		rm -f /tmp/release_notes.md; \
		echo "✅ GitHub Release created successfully!"; \
	else \
		echo "❌ Error: Tag v$$CURRENT_VERSION not found"; \
		echo "💡 Run 'make bump-patch' (or bump-minor/major) first to create the tag"; \
		exit 1; \
	fi

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