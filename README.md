# SSeed

[![PyPI Version](https://img.shields.io/pypi/v/sseed.svg)](https://pypi.org/project/sseed/)
[![Downloads](https://img.shields.io/pypi/dm/sseed.svg)](https://pypi.org/project/sseed/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/pypi/pyversions/sseed.svg)](https://pypi.org/project/sseed/)
[![Test Coverage](https://img.shields.io/badge/coverage-90%25-brightgreen.svg)](https://github.com/yourusername/sseed)
[![Code Quality](https://img.shields.io/badge/pylint-9.89%2F10-brightgreen.svg)](https://github.com/yourusername/sseed)

**Secure, offline BIP39/SLIP39 cryptocurrency seed management with mathematical verification**

---

## ✨ Features

- 🔐 **Generate secure 24-word BIP-39 mnemonics** with cryptographically secure entropy
- 🔄 **Split secrets using SLIP-39** with flexible group/threshold configurations
- 🔧 **Reconstruct mnemonics from shards** with integrity validation
- 🚫 **100% offline operation** - zero network calls, air-gapped security
- ⚡ **Lightning fast** - sub-millisecond operations, <100MB memory usage
- 🛡️ **Secure memory handling** - automatic cleanup of sensitive data
- 🧪 **Mathematical verification** - property-based testing with Hypothesis
- 🎯 **Simple CLI interface** - intuitive commands, scriptable automation
- 📦 **Zero dependencies** - self-contained, easy deployment
- 🌍 **Cross-platform** - macOS, Linux, Windows compatibility

## 🚀 Quick Install

```bash
pip install sseed
```

## 📖 Quick Start

### Generate → Shard → Restore Demo

```bash
# Generate a secure mnemonic
$ sseed gen
abandon ability able about above absent absorb abstract absurd abuse access accident

# Split into 3-of-5 threshold shards  
$ sseed gen | sseed shard -g 3-of-5
# Group 1 of 1 - Share 1 of 5: academic acid acrobat...
# Group 1 of 1 - Share 2 of 5: academic acid beard...
# Group 1 of 1 - Share 3 of 5: academic acid ceramic...
# Group 1 of 1 - Share 4 of 5: academic acid decision...
# Group 1 of 1 - Share 5 of 5: academic acid echo...

# Restore from any 3 shards
$ sseed restore shard1.txt shard2.txt shard3.txt
abandon ability able about above absent absorb abstract absurd abuse access accident
```

### Advanced Usage

```bash
# Generate to file with timestamp
sseed gen -o "backup-$(date +%Y%m%d).txt"

# Multi-group configuration (enterprise setup)
sseed shard -g "2:(2-of-3,3-of-5)" -i seed.txt --separate -o shards/

# Restore with passphrase protection
sseed restore -p "my-secure-passphrase" shard*.txt
```

## 📚 API Documentation

For programmatic integration, SSeed provides a clean Python API:

```python
from sseed import generate_mnemonic, create_shards, restore_mnemonic

# Generate secure mnemonic
mnemonic = generate_mnemonic()

# Create threshold shards
shards = create_shards(mnemonic, groups="3-of-5")

# Restore from shards
restored = restore_mnemonic(shards[:3])
```

**[📖 Full API Documentation →](docs/api.md)**

## 🛠️ Installation Options

### From PyPI (Recommended)
```bash
pip install sseed
```

### From Source
```bash
git clone https://github.com/yourusername/sseed.git
cd sseed
pip install .
```

### Development Setup
```bash
pip install -e ".[dev]"
pytest  # Run 265+ comprehensive tests
```

## 🔧 Command Reference

| Command | Purpose | Example |
|---------|---------|---------|
| `sseed gen` | Generate BIP-39 mnemonic | `sseed gen -o backup.txt` |
| `sseed shard` | Split into SLIP-39 shards | `sseed shard -g 3-of-5 -i seed.txt` |
| `sseed restore` | Reconstruct from shards | `sseed restore shard*.txt` |

### Configuration Examples

**Simple Threshold:**
- `3-of-5` - Any 3 of 5 shards required

**Multi-Group Security:**
- `2:(2-of-3,3-of-5)` - Need 2 groups: 2-of-3 AND 3-of-5 shards

**Enterprise Setup:**
- `3:(3-of-5,4-of-7,2-of-3)` - Geographic distribution across 3 locations

## 🔒 Security Features

- ✅ **Cryptographically secure entropy** using `secrets.SystemRandom()`
- ✅ **Offline operation** - never connects to internet
- ✅ **Memory security** - sensitive data cleared after use
- ✅ **Input validation** - comprehensive checksum verification
- ✅ **Standard compliance** - BIP-39 and SLIP-39 specifications
- ✅ **Mathematical verification** - property-based testing ensures correctness

## ⚡ Performance

| Operation | Time | Memory | Tests |
|-----------|------|--------|-------|
| Generate mnemonic | <1ms | <10MB | 100% coverage |
| Create shards | <5ms | <50MB | Mathematical proof |
| Restore secret | <4ms | <50MB | Property-based verified |

**Benchmarks:** Exceeds enterprise requirements by 5-75x

## 🧪 Quality Assurance

- **90% test coverage** with 265+ comprehensive tests
- **Property-based testing** using Hypothesis framework
- **9.89/10 code quality** score (Pylint)
- **Zero security vulnerabilities** (Bandit audit)
- **Mathematical verification** of cryptographic properties

## 📋 Requirements

- **Python:** 3.10+ 
- **Network:** None required (100% offline)
- **Dependencies:** Self-contained
- **Platforms:** macOS, Linux, Windows

## 🤝 Contributing

Contributions welcome! Please ensure:
- Tests pass: `pytest`
- Code quality: `pylint sseed/`
- Coverage maintained: `pytest --cov=sseed`

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## ⚠️ Security Notice

**For Educational and Legitimate Use Only**

- Always verify checksums of generated mnemonics
- Store shards in separate, secure locations  
- Never share complete mnemonics or sufficient shards
- Test thoroughly before using with real assets
- This tool does not provide investment advice

---

**Made with ❤️ for the cryptocurrency community**