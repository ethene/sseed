# Product Requirements Document (PRD)

## Project: sseed – Offline BIP39/SLIP39 CLI Tool

### 1. Objective
Create a minimalistic Python command-line tool that works fully offline to:
1. Generate a 24-word BIP-39 mnemonic using secure entropy.
2. Split the mnemonic into SLIP-39 shards with group/threshold configuration.
3. Reconstruct the mnemonic from a valid set of shards.

### 2. Functional Requirements

#### F-1: Entropy
- Use `secrets.SystemRandom().randbits(256)` or `secrets.token_bytes` for cryptographically secure entropy.
- No fallback to `random`.

#### F-2: BIP-39 Mnemonic Generation
- Use `bip_utils.Bip39MnemonicGenerator` to generate a 24-word mnemonic in English.

#### F-3: SLIP-39 Sharding
- Use the `slip39` library to split and restore mnemonics using SLIP-39.
- Allow custom group/threshold configurations.

#### F-4: Command Interface
- CLI commands:
    - `sseed gen [-o file]`
    - `sseed shard [-i seed.txt] [-g 3-of-5] [-o shards.txt]`
    - `sseed restore shard1.txt shard2.txt ...`
- Accept mnemonic or shards via stdin or file(s), output to stdout or file(s).

#### F-5: Validation
- Validate mnemonic checksum, shard integrity, threshold logic.
- Exit codes:
    - 0: Success
    - 1: Invalid usage or file error
    - 2: Cryptographic error (e.g., invalid seed or shard)

### 3. Non-Functional Requirements

#### Security
- No internet calls.
- Use secure memory handling and variable deletion (`del`) after usage.

#### Portability
- Compatible with Python 3.10+
- Cross-platform CLI: macOS, Linux, Windows

#### Usability
- Simple help via `-h`
- Clear error messages

#### Performance
- Execution time per operation < 50 ms
- RAM usage < 64 MB

### 4. Libraries / Dependencies
- `bip_utils` – for BIP-39 mnemonic generation
- `slip39` – for SLIP-39 sharding and recovery
- `argparse` – command-line parsing (std-lib)
- `secrets`, `os`, `sys` – for entropy and secure handling
- `pytest`, `mypy`, `ruff`, `bandit` – for testing, linting, and security auditing

### 5. Edge Cases
- Handle duplicate shards on restore
- Reject invalid shard count or checksum
- Normalize input (NFKD)

### 6. File Formats
- Plain text UTF-8
- First line: mnemonic or shard
- Comments: lines starting with `#`

### 7. Testing
- Test round-trip (gen → shard → restore)
- Test with wrong checksum
- Test under threshold
- Fuzz test: 100k seeds → unique check

### 8. Optional Features (Future)
- QR-code shard output
- GUI wrapper
- Optional hardware RNG (e.g., via pyhidapi)