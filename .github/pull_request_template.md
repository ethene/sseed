# Pull Request

## Description
Brief description of changes and why they are needed.

## Type of Change
- [ ] 🐛 Bug fix (non-breaking change that fixes an issue)
- [ ] ✨ New feature (non-breaking change that adds functionality)
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] 📚 Documentation update
- [ ] 🔧 Code maintenance (refactoring, performance improvements, etc.)
- [ ] 🧪 Test additions or improvements
- [ ] 🔒 Security improvement

## Testing
- [ ] I have tested these changes locally
- [ ] Tests pass: `make test` or `make ci-test`
- [ ] Coverage remains ≥90%: `pytest --cov=sseed --cov-report=term-missing`
- [ ] Property-based tests pass (if applicable)

## Code Quality
- [ ] Code follows PEP 8 style guidelines: `make check`
- [ ] Type hints are provided: `mypy sseed/`
- [ ] Linting passes: `pylint sseed/ --fail-under=9.5`
- [ ] No new security issues: `bandit -r sseed/`

## Cryptographic Security (if applicable)
- [ ] Cryptographic operations use secure randomness
- [ ] No sensitive data is logged or exposed
- [ ] Changes maintain offline-first security model
- [ ] Threshold security properties preserved (for SLIP-39 changes)

## Documentation
- [ ] Code is self-documenting with clear variable/function names
- [ ] Docstrings added/updated (Google style)
- [ ] README updated (if needed)
- [ ] CHANGELOG.md updated with user-facing changes

## Additional Notes
Any additional context, edge cases, or considerations for reviewers.

---

**Review Checklist for Maintainers:**
- [ ] Code review completed
- [ ] Security implications considered
- [ ] Performance impact assessed
- [ ] Breaking changes documented
- [ ] Version bump needed (patch/minor/major) 