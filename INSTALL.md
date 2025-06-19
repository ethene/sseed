# SSeed Installation Guide

## Method 1: Install from PyPI (Recommended)

```bash
pip install sseed
```

## Method 2: Install from Source

```bash
git clone <repository-url>
cd sseed
pip install .
```

## Method 3: Development Installation

```bash
git clone <repository-url>
cd sseed
pip install -e ".[dev]"
```

## Verification

After installation, verify sseed is working:

```bash
# Check help
sseed --help

# Generate a test mnemonic
sseed gen

# Test all functionality
sseed gen -o test_seed.txt
sseed shard -i test_seed.txt -g 3-of-5 -o test_shards.txt
head -3 test_shards.txt | sseed restore
rm test_seed.txt test_shards.txt
```

## Requirements

- Python 3.10 or higher
- No internet connection required for operation

## Troubleshooting

### Command not found

If `sseed` command is not found after installation:

1. Check if pip installed to the right location:
   ```bash
   pip show sseed
   ```

2. Make sure your Python scripts directory is in PATH:
   ```bash
   python -m pip show --files sseed | grep -E "(bin|Scripts)"
   ```

3. Try running as a module:
   ```bash
   python -m sseed --help
   ```

### Import errors

If you get import errors, ensure all dependencies are installed:

```bash
pip install --upgrade sseed
```

Or for development:

```bash
pip install -e ".[dev]"
```

## Uninstallation

```bash
pip uninstall sseed
``` 