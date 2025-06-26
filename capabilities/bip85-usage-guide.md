# BIP85 Usage Guide

## Quick Start

BIP85 enables you to generate unlimited child wallets, passwords, and cryptographic keys from a single master mnemonic. This provides a hierarchical backup system where one master seed protects all your derived secrets.

### Basic Workflow

```bash
# 1. Generate or use existing master mnemonic
sseed gen -o master.txt

# 2. Generate child wallets
sseed bip85 bip39 -i master.txt -w 12 -n 0 -o wallet1.txt
sseed bip85 bip39 -i master.txt -w 12 -n 1 -o wallet2.txt

# 3. Generate application keys
sseed bip85 hex -i master.txt -b 32 -n 0 -o app_key.hex

# 4. Generate secure passwords
sseed bip85 password -i master.txt -l 20 -c base64 -n 0 -o app.pwd
```

## Applications

### BIP39 Mnemonic Generation

Generate child BIP39 mnemonics for unlimited independent wallets:

```bash
# 12-word English child mnemonic (most common)
sseed bip85 bip39 -i master.txt -w 12 -n 0

# 24-word high-security child mnemonic
sseed bip85 bip39 -i master.txt -w 24 -n 0

# Multi-language child wallets
sseed bip85 bip39 -i master.txt -w 12 -l es -n 1    # Spanish
sseed bip85 bip39 -i master.txt -w 12 -l zh-cn -n 2 # Chinese
sseed bip85 bip39 -i master.txt -w 12 -l ko -n 3    # Korean
```

**Word Count Options:** 12, 15, 18, 21, 24  
**Language Options:** en, es, fr, it, pt, cs, zh-cn, zh-tw, ko  
**Index Range:** 0 to 2³¹-1 (2,147,483,647)

### Hex Entropy Generation

Generate raw entropy bytes for encryption keys, tokens, and random data:

```bash
# 32-byte (256-bit) encryption key
sseed bip85 hex -i master.txt -b 32 -n 0

# 16-byte (128-bit) token
sseed bip85 hex -i master.txt -b 16 -n 1

# Uppercase hex output
sseed bip85 hex -i master.txt -b 24 -u -n 2
```

**Byte Range:** 16-64 bytes  
**Format Options:** lowercase (default), uppercase (-u)

### Password Generation

Generate secure passwords with various character sets:

```bash
# Base64 password (URL-safe)
sseed bip85 password -i master.txt -l 20 -c base64 -n 0

# Alphanumeric password (A-Z, a-z, 0-9)
sseed bip85 password -i master.txt -l 16 -c alphanumeric -n 1

# Full ASCII password (all printable characters)
sseed bip85 password -i master.txt -l 25 -c ascii -n 2

# Base85 password (high entropy)
sseed bip85 password -i master.txt -l 30 -c base85 -n 3
```

**Character Sets:**
- `base64`: A-Z, a-z, 0-9, -, _ (64 chars)
- `base85`: ASCII85 character set (85 chars)
- `alphanumeric`: A-Z, a-z, 0-9 (62 chars)
- `ascii`: All printable ASCII (94 chars)

**Length Range:** 10-128 characters

## Advanced Workflows

### Multi-Purpose Master Seed

```bash
# Master setup
sseed gen -o master.txt

# Personal wallets
sseed bip85 bip39 -i master.txt -w 12 -n 0 -o personal_main.txt
sseed bip85 bip39 -i master.txt -w 12 -n 1 -o personal_cold.txt

# Business wallets
sseed bip85 bip39 -i master.txt -w 24 -n 10 -o business_main.txt
sseed bip85 bip39 -i master.txt -w 24 -n 11 -o business_treasury.txt

# Application keys
sseed bip85 hex -i master.txt -b 32 -n 100 -o app1_encryption.key
sseed bip85 hex -i master.txt -b 32 -n 101 -o app2_signing.key

# Service passwords
sseed bip85 password -i master.txt -l 32 -c base64 -n 200 -o database.pwd
sseed bip85 password -i master.txt -l 20 -c alphanumeric -n 201 -o api.pwd
```

### Geographic Distribution

```bash
# Generate master in secure location
sseed gen -o master.txt

# Create region-specific child wallets
sseed bip85 bip39 -i master.txt -w 12 -l en -n 0 -o us_wallet.txt      # US
sseed bip85 bip39 -i master.txt -w 12 -l es -n 1 -o latam_wallet.txt   # Latin America
sseed bip85 bip39 -i master.txt -w 12 -l zh-cn -n 2 -o asia_wallet.txt # Asia

# Distribute region-specific wallets to local teams
# Each region gets their native language wallet
```

### BIP85 + SLIP39 Security

Combine BIP85 child generation with SLIP39 sharding for enterprise security:

```bash
# Generate high-value wallet and immediately shard it
sseed bip85 bip39 -i master.txt -w 24 -n 0 | sseed shard -g 3-of-5

# Generate treasury wallet with multi-group sharding
sseed bip85 bip39 -i master.txt -w 24 -n 1 | sseed shard -g "2:(2-of-3,3-of-5)"

# Generate operational wallet for daily use (no sharding needed)
sseed bip85 bip39 -i master.txt -w 12 -n 2 -o operational.txt
```

## Index Management

### Index Organization Strategy

```bash
# Personal wallets: 0-99
sseed bip85 bip39 -i master.txt -w 12 -n 0  # Main personal
sseed bip85 bip39 -i master.txt -w 12 -n 1  # Backup personal
sseed bip85 bip39 -i master.txt -w 12 -n 2  # DeFi personal

# Business wallets: 100-199  
sseed bip85 bip39 -i master.txt -w 24 -n 100  # Main business
sseed bip85 bip39 -i master.txt -w 24 -n 101  # Business treasury
sseed bip85 bip39 -i master.txt -w 24 -n 102  # Business operations

# Application keys: 1000-1999
sseed bip85 hex -i master.txt -b 32 -n 1000  # App1 encryption
sseed bip85 hex -i master.txt -b 32 -n 1001  # App1 signing
sseed bip85 hex -i master.txt -b 32 -n 1010  # App2 encryption

# Passwords: 2000-2999
sseed bip85 password -i master.txt -l 32 -n 2000  # Database admin
sseed bip85 password -i master.txt -l 20 -n 2001  # API service
sseed bip85 password -i master.txt -l 16 -n 2002  # Development
```

### Index Documentation

Keep a secure record of your index allocation:

```
BIP85 Index Allocation
=====================

Personal Wallets (0-99):
  0: Main wallet (12 words, English)
  1: Cold storage (24 words, English)
  2: DeFi wallet (12 words, English)

Business Wallets (100-199):
  100: Main business (24 words, English)
  101: Treasury (24 words, English)
  102: Operations (12 words, English)

Application Keys (1000-1999):
  1000: App1 encryption key (32 bytes)
  1001: App1 signing key (32 bytes)
  1010: App2 encryption key (32 bytes)

Passwords (2000-2999):
  2000: Database admin (32 chars, base64)
  2001: API service (20 chars, alphanumeric)
  2002: Development env (16 chars, base64)
```

## Security Best Practices

### Master Seed Protection

- **Never expose master seed** - Only derive children as needed
- **Air-gapped generation** - Generate master on offline device
- **Multiple backups** - Store master seed backups in separate locations
- **Steel backup** - Consider metal seed storage for master
- **Passphrase protection** - Use 25th word for additional security

### Child Seed Management

- **Index tracking** - Maintain secure record of index assignments
- **Purpose separation** - Use different index ranges for different purposes
- **Regular rotation** - Periodically rotate application keys and passwords
- **Access control** - Limit who has access to master vs. child seeds

### Operational Security

```bash
# Generate master on air-gapped machine
sseed gen -o master.txt

# Transfer master to secure storage
# Generate children on operational machines as needed

# For high-security applications, derive children on air-gapped machine
sseed bip85 bip39 -i master.txt -w 24 -n 0 -o treasury.txt

# Transfer only child seeds to operational systems
```

## Integration Examples

### Wallet Setup Script

```bash
#!/bin/bash
# wallet_setup.sh - Generate complete wallet infrastructure

MASTER_FILE="master.txt"
INDEX_START=0

# Personal wallets
echo "Generating personal wallets..."
sseed bip85 bip39 -i "$MASTER_FILE" -w 12 -n $((INDEX_START + 0)) -o personal_main.txt
sseed bip85 bip39 -i "$MASTER_FILE" -w 12 -n $((INDEX_START + 1)) -o personal_backup.txt
sseed bip85 bip39 -i "$MASTER_FILE" -w 12 -n $((INDEX_START + 2)) -o personal_defi.txt

# Generate application keys
echo "Generating application keys..."
sseed bip85 hex -i "$MASTER_FILE" -b 32 -n 1000 -o app_encryption.key
sseed bip85 hex -i "$MASTER_FILE" -b 32 -n 1001 -o app_signing.key

# Generate service passwords
echo "Generating service passwords..."
sseed bip85 password -i "$MASTER_FILE" -l 32 -c base64 -n 2000 -o db_admin.pwd
sseed bip85 password -i "$MASTER_FILE" -l 20 -c alphanumeric -n 2001 -o api.pwd

echo "Wallet infrastructure ready!"
```

### Key Rotation Script

```bash
#!/bin/bash
# key_rotation.sh - Rotate application keys monthly

MASTER_FILE="master.txt"
ROTATION_EPOCH=$(date +%Y%m)  # YYYYMM format

# Rotate based on current month
BASE_INDEX=$((3000 + ROTATION_EPOCH))

echo "Rotating keys for epoch: $ROTATION_EPOCH"
sseed bip85 hex -i "$MASTER_FILE" -b 32 -n $BASE_INDEX -o current_app.key
sseed bip85 password -i "$MASTER_FILE" -l 32 -c base64 -n $((BASE_INDEX + 1)) -o current_api.pwd
```

## Troubleshooting

### Common Issues

**Same output for different commands:**
- Verify index (`-n`) is different
- Check application type (bip39/hex/password)
- Ensure parameter differences (word count, byte length, etc.)

**Cannot reproduce previous output:**
- Verify master seed is identical
- Check all parameters match exactly
- Confirm index value is correct

**Integration with other tools:**
- BIP85 output is standard-compliant
- Child mnemonics work with any BIP39-compatible wallet
- Hex output can be used with any application expecting entropy

### Verification

```bash
# Verify deterministic output
OUTPUT1=$(sseed bip85 bip39 -i master.txt -w 12 -n 0)
OUTPUT2=$(sseed bip85 bip39 -i master.txt -w 12 -n 0)
[ "$OUTPUT1" = "$OUTPUT2" ] && echo "✅ Deterministic" || echo "❌ Non-deterministic"

# Test different indices produce different output
OUTPUT_A=$(sseed bip85 bip39 -i master.txt -w 12 -n 0)
OUTPUT_B=$(sseed bip85 bip39 -i master.txt -w 12 -n 1)
[ "$OUTPUT_A" != "$OUTPUT_B" ] && echo "✅ Independent" || echo "❌ Collision"
```

## Further Reading

- **[BIP85 Specification](https://github.com/bitcoin/bips/blob/master/bip-0085.mediawiki)** - Official Bitcoin Improvement Proposal
- **[Complete Capability Documentation](./bip85-deterministic-entropy.md)** - Technical implementation details
- **[Production Deployment Guide](./bip85-production-guide.md)** - Enterprise deployment instructions
- **[CLI Examples](../sseed/cli/examples.py)** - Comprehensive usage examples 