# Refactoring Plan for SSeed v1.6.x

## Overview

This document outlines the comprehensive refactoring plan for SSeed v1.6.x to improve code organization, maintainability, and extensibility while preparing for future professional features.

### Goals
- Split monolithic modules into focused, single-responsibility components
- Improve code maintainability and testability
- Reduce code duplication and standardize patterns
- Prepare architecture for professional CLI features (v1.7+)
- Maintain 100% backward compatibility

### Scope
- **Primary Target**: CLI module (921 lines) - critical for extensibility
- **Secondary Targets**: File operations (502 lines), Validation (408 lines)
- **Timeline**: 4 stages over 2-3 weeks
- **Risk Level**: Medium (extensive but well-contained changes)

---

## Current State Analysis

### Code Size Distribution
```
sseed/cli.py              921 lines  (CRITICAL - requires immediate refactoring)
sseed/file_operations.py  502 lines  (HIGH - mixed responsibilities)
sseed/validation.py       408 lines  (MEDIUM - multiple concerns)
sseed/slip39_operations.py 374 lines (LOW - well-organized)
sseed/bip39.py            342 lines  (LOW - good structure)
```

### Identified Issues

#### CLI Module (921 lines)
**Problems:**
- Monolithic structure with 5 different responsibilities
- Command handlers with 80-150 lines each
- Repeated error handling patterns (4x duplication)
- Argument parsing mixed with business logic
- Examples and help text embedded in main module

**Impact:**
- Difficult to add new commands
- Hard to test individual commands
- Code duplication across handlers
- Blocks implementation of professional features

#### File Operations (502 lines)
**Problems:**
- Mixed reading/writing/formatting responsibilities
- Repeated file I/O patterns
- Comment generation embedded in writers
- Similar logic for different file types

**Impact:**
- Difficult to add new file formats
- Hard to modify file structure
- Testing requires complex setup

#### Validation Module (408 lines)
**Problems:**
- Multiple validation types in single file
- Unicode normalization mixed with business logic
- Different validation concerns coupled

**Impact:**
- Hard to extend validation rules
- Complex error handling
- Difficult to test individual validators

---

## Refactoring Strategy

### Stage 1: CLI Command Structure (v1.6.1)
**Priority**: CRITICAL
**Effort**: 2-3 days
**Risk**: Medium

#### Detailed Analysis Results

**Current CLI Structure (921 lines):**
```
Import/constants:             68 lines  (lines 1-69)
handle_version_command:       81 lines  (lines 70-150)  
show_examples:                73 lines  (lines 151-223)
create_parser:               245 lines  (lines 224-468) ← LARGEST FUNCTION
handle_gen_command:           90 lines  (lines 469-558)
handle_shard_command:         99 lines  (lines 559-657)
handle_restore_command:      108 lines  (lines 658-765)
handle_seed_command:          81 lines  (lines 766-846)
main:                         76 lines  (lines 847-922)
```

**Identified Patterns:**
- **Error Handling Duplication**: 4 identical error handling blocks across command handlers
- **Argument Parser Complexity**: 245-line `create_parser()` with 5 subparsers mixed together
- **Command Dispatch**: Simple if/elif chain in `main()` - ready for registry pattern
- **Shared Logic**: File I/O, entropy display, secure deletion patterns repeated

#### Objective
Split monolithic CLI into command-based architecture to enable future command additions.

#### Target Structure
```
sseed/
├── cli/
│   ├── __init__.py           # Public CLI interface (maintains compatibility)
│   ├── parser.py             # Base parser + global args (80 lines)
│   ├── examples.py           # Example display logic (80 lines)
│   ├── error_handling.py     # Common error handling patterns (60 lines)
│   └── commands/
│       ├── __init__.py       # Command registry and discovery (40 lines)
│       ├── base.py           # Base command class with common patterns (100 lines)
│       ├── gen.py            # Generate command handler + parser (120 lines)
│       ├── shard.py          # Shard command handler + parser (130 lines)
│       ├── restore.py        # Restore command handler + parser (140 lines)
│       ├── seed.py           # Seed command handler + parser (110 lines)
│       └── version.py        # Version command handler + parser (100 lines)
```

#### Implementation Tasks

**Task 1.1: Create Base Infrastructure (Day 1 Morning)**
- Create `sseed/cli/` package
- Extract `EXIT_*` constants to `cli/__init__.py` 
- Create `error_handling.py` with standardized error handling patterns:
  ```python
  def handle_crypto_errors(func):
      """Decorator for standardized cryptographic error handling."""
      
  def handle_file_errors(func):
      """Decorator for standardized file error handling."""
      
  def handle_validation_errors(func):
      """Decorator for standardized validation error handling."""
  ```

**Task 1.2: Base Command Class (Day 1 Afternoon)**
- Implement `base.py` with `BaseCommand` class:
  ```python
  class BaseCommand:
      def __init__(self, name: str, help: str):
          self.name = name
          self.help = help
      
      def add_arguments(self, parser) -> None:
          """Add command-specific arguments."""
          
      def handle(self, args: argparse.Namespace) -> int:
          """Execute command logic."""
          
      def handle_input(self, args) -> str:
          """Common input handling (file vs stdin)."""
          
      def handle_output(self, content: str, args) -> None:
          """Common output handling (file vs stdout)."""
  ```

**Task 1.3: Extract Command Handlers (Day 2)**
- Move `handle_version_command()` to `commands/version.py` with argument parsing
- Move `handle_gen_command()` to `commands/gen.py` with argument parsing  
- Move `handle_shard_command()` to `commands/shard.py` with argument parsing
- Move `handle_restore_command()` to `commands/restore.py` with argument parsing
- Move `handle_seed_command()` to `commands/seed.py` with argument parsing
- Each command class handles both argument setup and execution

**Task 1.4: Parser Restructuring (Day 2 Afternoon)**
- Create `parser.py` with base parser and global arguments (first 68 lines of `create_parser()`)
- Move command-specific parser setup to respective command classes
- Implement dynamic subparser registration system

**Task 1.5: Command Registry System (Day 3 Morning)**
- Implement command discovery in `commands/__init__.py`:
  ```python
  from .gen import GenCommand
  from .shard import ShardCommand
  from .restore import RestoreCommand
  from .seed import SeedCommand
  from .version import VersionCommand
  
  COMMANDS = {
      'gen': GenCommand,
      'shard': ShardCommand,
      'restore': RestoreCommand,
      'seed': SeedCommand,
      'version': VersionCommand,
  }
  ```

**Task 1.6: Main Function Refactoring (Day 3 Afternoon)**
- Update `main()` to use command registry instead of if/elif chain
- Move `show_examples()` to `examples.py`
- Implement backward compatibility layer in `cli/__init__.py`

#### Success Criteria
- All existing CLI commands work identically
- New commands can be added by creating single file in `commands/`
- Common error handling patterns standardized (4 duplicate blocks → 1 decorator system)
- CLI tests pass without modification  
- Import compatibility maintained: `from sseed.cli import main`
- Argument parser complexity reduced: 245 lines → ~80 lines base + ~25 lines per command

#### Detailed Migration Strategy

**Phase 1.1: Backward Compatibility Layer**
```python
# sseed/cli/__init__.py - maintains all existing exports
from .main import main
from .commands.gen import handle_gen_command  # Compatibility wrapper
from .commands.shard import handle_shard_command  # Compatibility wrapper
# ... etc for all handlers

# Exit codes (moved from cli.py)
EXIT_SUCCESS = 0
EXIT_USAGE_ERROR = 1
EXIT_CRYPTO_ERROR = 2
EXIT_FILE_ERROR = 3
EXIT_VALIDATION_ERROR = 4
EXIT_INTERRUPTED = 130
```

**Phase 1.2: Command Class Template**
```python
# sseed/cli/commands/gen.py
from sseed.cli.base import BaseCommand
from sseed.cli.error_handling import handle_crypto_errors, handle_file_errors

class GenCommand(BaseCommand):
    def __init__(self):
        super().__init__("gen", "Generate a 24-word BIP-39 mnemonic")
    
    def add_arguments(self, parser):
        parser.add_argument("-o", "--output", help="Output file")
        parser.add_argument("--show-entropy", action="store_true")
    
    @handle_crypto_errors
    @handle_file_errors
    def handle(self, args):
        # Original handle_gen_command logic here
        pass

# Compatibility function for existing imports
def handle_gen_command(args):
    """Backward compatibility wrapper."""
    return GenCommand().handle(args)
```

#### Error Pattern Standardization

**Before (4 duplicate blocks × 20 lines = 80 lines):**
```python
# Repeated in every command handler:
except (EntropyError, MnemonicError, SecurityError) as e:
    logger.error("Cryptographic error during generation: %s", e)
    print(f"Cryptographic error: {e}", file=sys.stderr)
    return EXIT_CRYPTO_ERROR
except FileError as e:
    logger.error("File I/O error during generation: %s", e)
    print(f"File error: {e}", file=sys.stderr)
    return EXIT_FILE_ERROR
# ... etc
```

**After (1 decorator system = 60 lines total):**
```python
# sseed/cli/error_handling.py
def handle_common_errors(operation_name: str):
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except (EntropyError, MnemonicError, SecurityError) as e:
                logger.error(f"Cryptographic error during {operation_name}: %s", e)
                print(f"Cryptographic error: {e}", file=sys.stderr)
                return EXIT_CRYPTO_ERROR
            except FileError as e:
                logger.error(f"File I/O error during {operation_name}: %s", e)
                print(f"File error: {e}", file=sys.stderr)
                return EXIT_FILE_ERROR
            # ... etc
        return wrapper
    return decorator

# Usage in commands:
@handle_common_errors("generation")
def handle(self, args):
    # Command logic without error handling boilerplate
```

#### Code Size Reduction

**Expected Results:**
- **Total Lines**: 921 lines → ~900 lines (distributed across modules)
- **Largest Single File**: 245 lines (`create_parser`) → 140 lines (largest command)
- **Error Handling**: 80 lines duplicated → 60 lines centralized
- **Main Function**: 76 lines → 40 lines (simplified dispatch)
- **Argument Parsing**: 245 lines → 80 base + 25 per command (modular)

**New Command Addition Effort:**
- **Before**: Modify 3 functions in 921-line file (high risk)
- **After**: Add single 100-line file in `commands/` (low risk)

---

### Stage 2: File Operations Structure (v1.6.2)
**Priority**: HIGH
**Effort**: 1-2 days
**Risk**: Low

#### Objective
Separate file I/O concerns to enable new file formats and improve maintainability.

#### Target Structure
```
sseed/
├── file_operations/
│   ├── __init__.py           # Public interface (backward compatibility)
│   ├── readers.py            # All reading operations
│   ├── writers.py            # All writing operations
│   ├── formatters.py         # Comment and format generation
│   └── validators.py         # File content validation
```

#### Implementation Tasks

**Task 2.1: Extract Reading Operations**
- Move `read_mnemonic_from_file()` to `readers.py`
- Move `read_shard_from_file()` to `readers.py`
- Move `read_shards_from_files()` to `readers.py`
- Move `read_from_stdin()` to `readers.py`

**Task 2.2: Extract Writing Operations**
- Move `write_mnemonic_to_file()` to `writers.py`
- Move `write_shards_to_file()` to `writers.py`
- Move `write_shards_to_separate_files()` to `writers.py`
- Move `write_to_stdout()` to `writers.py`

**Task 2.3: Extract Format Generation**
- Create `formatters.py` with comment generation
- Extract file header generation logic
- Create format-specific writers (BIP39, SLIP39)

**Task 2.4: File Validation**
- Create `validators.py` for file content validation
- Extract file format detection
- Implement file integrity checking

#### Success Criteria
- All file operations work identically
- New file formats can be added easily
- File I/O testing simplified
- Backward compatibility maintained
- Common formatting patterns reusable

---

### Stage 3: Validation Structure (v1.6.3)
**Priority**: MEDIUM
**Effort**: 1-2 days
**Risk**: Low

#### Objective
Organize validation by concern type to improve extensibility and clarity.

#### Target Structure
```
sseed/
├── validation/
│   ├── __init__.py           # Public interface (backward compatibility)
│   ├── input.py              # Input normalization and format validation
│   ├── crypto.py             # Cryptographic validation (checksums, etc.)
│   └── structure.py          # Structure validation (groups, shards, etc.)
```

#### Implementation Tasks

**Task 3.1: Input Validation**
- Move `normalize_input()` to `input.py`
- Move `validate_mnemonic_words()` to `input.py`
- Move `sanitize_filename()` to `input.py`
- Add enhanced input validation functions

**Task 3.2: Cryptographic Validation**
- Move `validate_mnemonic_checksum()` to `crypto.py`
- Create enhanced checksum validation
- Add entropy quality validation functions

**Task 3.3: Structure Validation**
- Move `validate_group_threshold()` to `structure.py`
- Move `validate_shard_integrity()` to `structure.py`
- Move `detect_duplicate_shards()` to `structure.py`
- Add multi-group validation

#### Success Criteria
- All validation functions work identically
- New validation rules can be added easily
- Validation testing simplified
- Clear separation of validation types
- Backward compatibility maintained

---

### Stage 4: Integration and Optimization (v1.6.4)
**Priority**: HIGH
**Effort**: 1-2 days
**Risk**: Low

#### Objective
Complete integration, optimize imports, and prepare for v1.7 features.

#### Implementation Tasks

**Task 4.1: Import Optimization**
- Update all internal imports to use new structure
- Optimize import paths for performance
- Ensure backward compatibility maintained
- Update `__init__.py` files with proper exports

**Task 4.2: Documentation Updates**
- Update docstrings to reflect new architecture
- Create architectural documentation
- Update contribution guidelines for new structure

**Task 4.3: Test Suite Updates**
- Update test imports to use new structure
- Add tests for new architectural components
- Ensure 100% test coverage maintained
- Add integration tests for refactored components

**Task 4.4: Performance Validation**
- Benchmark import performance
- Validate memory usage patterns
- Ensure no performance regressions
- Optimize critical paths

**Task 4.5: Future-Proofing**
- Prepare command structure for v1.7 features
- Design extension points for new validators
- Create plugin architecture foundation
- Document extension patterns

#### Success Criteria
- All existing functionality works identically
- No performance regressions
- Test suite passes with 100% coverage
- Clean import structure
- Ready for v1.7 feature additions

---

## Testing Strategy

### Backward Compatibility Testing
```bash
# Ensure all existing imports work
python -c "from sseed.cli import main; from sseed.file_operations import *; from sseed.validation import *"

# Run complete test suite
make test

# Validate CLI compatibility
sseed gen -o test.txt
sseed shard -i test.txt -g 3-of-5 --separate -o shards
sseed restore shard*.txt
```

### New Architecture Testing
```bash
# Test new command structure
python -c "from sseed.cli.commands.gen import GenCommand"

# Test new file operations
python -c "from sseed.file_operations.readers import read_mnemonic_from_file"

# Test new validation structure  
python -c "from sseed.validation.crypto import validate_mnemonic_checksum"
```

### Performance Testing
```bash
# Benchmark import times
python -c "import time; start=time.time(); import sseed; print(f'Import time: {time.time()-start:.3f}s')"

# Memory usage validation
python -c "import psutil, sseed; print(f'Memory: {psutil.Process().memory_info().rss/1024/1024:.1f}MB')"
```

---

## Risk Mitigation

### High-Risk Areas
1. **CLI Import Compatibility**: Ensure existing scripts continue working
2. **Test Suite Updates**: Extensive import changes require careful test updates
3. **Performance Impact**: Multiple new imports could slow startup

### Mitigation Strategies
1. **Gradual Migration**: Stage implementation over 4 releases
2. **Compatibility Layer**: Maintain old import paths during transition
3. **Comprehensive Testing**: Test suite updates parallel with refactoring
4. **Performance Monitoring**: Benchmark each stage for regressions

### Rollback Plan
Each stage is independently deployable with rollback capability:
- Stage 1: Rollback to monolithic CLI if command system fails
- Stage 2: Rollback to single file_operations.py if file handling breaks
- Stage 3: Rollback to single validation.py if validation fails
- Stage 4: Rollback any optimization that causes regressions

---

## Future Benefits

### v1.7 Feature Enablement
With this refactoring complete, v1.7 features become straightforward:

```python
# New commands are simple to add
# sseed/cli/commands/analyze.py
class AnalyzeCommand(BaseCommand):
    def handle(self, args):
        # Advanced mnemonic analysis implementation
        pass

# New file formats are easy to support
# sseed/file_operations/formatters.py
class JSONFormatter(BaseFormatter):
    def format_mnemonic(self, mnemonic, metadata):
        # JSON output formatting
        pass

# New validation rules are modular
# sseed/validation/crypto.py
def validate_entropy_quality(entropy_bytes):
    # Entropy quality scoring implementation
    pass
```

### Professional CLI Readiness
- Command plugin architecture ready
- Validation framework extensible
- File format system modular
- Error handling standardized

### Development Velocity Improvements
- **New Commands**: 1 day instead of 1 week
- **New File Formats**: 2 hours instead of 2 days
- **New Validation**: 1 hour instead of 4 hours
- **Testing**: Isolated module testing instead of integration-heavy testing

---

## Implementation Timeline

### Week 1
- **Days 1-2**: Stage 1 - CLI Command Structure
- **Day 3**: Stage 2 - File Operations Structure
- **Days 4-5**: Testing and validation

### Week 2
- **Days 1-2**: Stage 3 - Validation Structure
- **Days 3-4**: Stage 4 - Integration and Optimization
- **Day 5**: Final testing and documentation

### Release Schedule
- **v1.6.1**: CLI refactoring (Stage 1)
- **v1.6.2**: File operations refactoring (Stage 2)
- **v1.6.3**: Validation refactoring (Stage 3)
- **v1.6.4**: Integration complete (Stage 4)

This refactoring plan positions SSeed for the professional features planned in v1.7 while maintaining stability and backward compatibility throughout the transition. 