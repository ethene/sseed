# Custom Entropy Security Guidelines

## Overview
Custom entropy sources allow advanced users to provide their own randomness for mnemonic generation. This feature comes with significant security responsibilities and should only be used by those who fully understand the cryptographic implications.

## Security Principles

### Quality Requirements
SSeed implements comprehensive entropy quality validation with the following scoring system:

- **Score Range**: 0-100 (higher is better)
- **Acceptance Thresholds**:
  - `--allow-weak`: Minimum score 70/100 for general entropy, 60/100 for dice
  - `--force`: Overrides all quality checks (dangerous)
- **Quality Analysis**: Pattern detection, distribution analysis, weakness signatures

### Common Security Pitfalls

#### Critical Mistakes to Avoid

1. **Insufficient Entropy**
   ```bash
   # WRONG: Too few dice rolls
   sseed gen --entropy-dice "1,2,3,4,5,6" --force
   
   # CORRECT: Sufficient dice rolls for 24-word mnemonic
   sseed gen --entropy-dice "1,2,3,4,5,6,..." --force  # 60+ rolls needed
   ```

2. **Predictable Sources**
   ```bash
   # WRONG: Using timestamps or sequential data
   sseed gen --entropy-hex "0123456789abcdef..." --force
   ```

3. **Biased Sources**
   ```bash
   # WRONG: Unfair dice or biased sources
   sseed gen --entropy-dice "6,6,6,6,6,6,..." --force
   
   # CORRECT: Fair dice with proper randomization
   sseed gen --entropy-dice "3,1,4,6,2,5,..." --force
   ```

## Entropy Sources Comparison

| Source | Security Level | Ease of Use | Recommended Use |
|--------|---------------|-------------|-----------------|
| **System Random** | ★★★★★ | ★★★★★ | ✅ **Primary recommendation** |
| **Fair Dice** | ★★★★☆ | ★★☆☆☆ | ⚠️ Advanced users only |
| **Hardware RNG** | ★★★★★ | ★★☆☆☆ | ⚠️ If properly validated |
| **Hex Input** | ★☆☆☆☆ | ★★★☆☆ | ❌ Dangerous |

## Security Warnings and User Consent

### Two-Tier Consent System
SSeed implements a two-tier consent system for dangerous operations:

1. **`--allow-weak`**: Required for entropy with quality score < 70
2. **`--force`**: Required for entropy with quality score < 50 or other critical issues

### Warning Examples

```bash
⚠️ WARNING: Using custom hex entropy (NOT RECOMMENDED)
❌ SECURITY WARNING: Entropy quality insufficient (20/100)
```

## Best Practices

### For Hex Entropy
1. **Source Verification**: Ensure entropy comes from cryptographically secure source
2. **Length Requirements**: Provide at least 32 bytes (256 bits) for 24-word mnemonics
3. **Quality Testing**: Always use `--entropy-analysis` to verify quality
4. **One-Time Use**: Never reuse the same hex entropy

### For Dice Entropy
1. **Fair Dice**: Use verified fair dice (casino-grade recommended)
2. **Sufficient Rolls**: Minimum 60 rolls for 24-word mnemonics
3. **Proper Randomization**: Ensure dice are properly shaken/randomized
4. **Recording Accuracy**: Double-check dice roll recording

## Conclusion

Custom entropy sources provide flexibility for advanced users but come with significant security responsibilities. The default system entropy (`sseed gen`) remains the recommended approach for most users.

**Remember**: Poor entropy quality can completely compromise wallet security, making funds permanently inaccessible or vulnerable to theft.
