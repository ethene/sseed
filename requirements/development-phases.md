# sseed Project - Development Steps

## Phase 1: Project Setup & Structure
1. Create project directory structure following user rules
2. Set up requirements.txt with exact package versions
3. Create pyproject.toml for project configuration
4. Set up logging configuration
5. Create main CLI entry point module

## Phase 2: Core Cryptographic Functions
6. Implement secure entropy generation using `secrets.SystemRandom()`
7. Create BIP-39 mnemonic generation using `bip_utils.Bip39MnemonicGenerator`
8. Implement input validation and normalization (NFKD)
9. Add secure memory handling and variable cleanup

## Phase 3: SLIP-39 Implementation
10. Implement SLIP-39 sharding using `slip39` library
11. Add group/threshold configuration support
12. Implement SLIP-39 reconstruction functionality
13. Add shard validation and integrity checks

## Phase 4: CLI Interface
14. Create argument parser using `argparse`
15. Implement `gen` command for mnemonic generation
16. Implement `shard` command for SLIP-39 sharding
17. Implement `restore` command for reconstruction
18. Add file I/O support (stdin/stdout and file operations)

## Phase 5: Validation & Error Handling
19. Implement mnemonic checksum validation
20. Add threshold logic validation
21. Implement duplicate shard detection
22. Create custom exception classes
23. Add comprehensive error handling with proper exit codes

## Phase 6: File Format Support
24. Implement plain text UTF-8 file format
25. Add comment support (lines starting with #)
26. Ensure cross-platform compatibility

## Phase 7: Testing Suite
27. Create unit tests for entropy generation
28. Add tests for BIP-39 mnemonic operations
29. Create SLIP-39 round-trip tests (gen → shard → restore)
30. Add edge case tests (wrong checksum, under threshold)
31. Implement fuzz testing (100k seeds → unique check)
32. Add integration tests for CLI commands

## Phase 8: Quality Assurance
33. Set up mypy type checking
34. Configure ruff linting
35. Run bandit security audit
36. Ensure PEP 8 compliance
37. Add docstrings (Google style) for all functions/classes

## Phase 9: Performance & Security
38. Verify execution time < 50ms per operation
39. Ensure RAM usage < 64MB
40. Implement secure memory handling
41. Verify no internet calls
42. Test cross-platform compatibility (macOS, Linux, Windows)

## Phase 10: Documentation & Polish
43. Create comprehensive help text (-h)
44. Ensure clear error messages
45. Add usage examples
46. Final testing and validation

## Required Exit Codes:
- 0: Success
- 1: Invalid usage or file error
- 2: Cryptographic error (invalid seed or shard) 