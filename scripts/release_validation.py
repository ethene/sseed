#!/usr/bin/env python3
"""
BIP85 Release Validation Script

Validates BIP85 implementation for production release.
"""

import sys
import subprocess
import tempfile
from pathlib import Path

def run_command(cmd):
    """Run command and return success status."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def validate_basic_functionality():
    """Test basic BIP85 functionality."""
    print("🧪 Testing basic BIP85 functionality...")
    
    # Test CLI help
    success, stdout, stderr = run_command(['python', '-m', 'sseed', 'bip85', '--help'])
    if not success:
        print(f"❌ CLI help failed: {stderr}")
        return False
    
    # Test with temp seed file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        test_seed = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
        f.write(test_seed)
        f.flush()
        
        # Test BIP39 generation
        success, stdout, stderr = run_command([
            'python', '-m', 'sseed', 'bip85', '-i', f.name, 
            'bip39', '-w', '12', '-n', '0'
        ])
        
        Path(f.name).unlink()  # Cleanup
        
        if not success:
            print(f"❌ BIP39 generation failed: {stderr}")
            return False
        
        # Extract the mnemonic line (it's the line that doesn't start with # or BIP85:)
        lines = stdout.strip().split('\n')
        mnemonic_lines = [line for line in lines if line and not line.startswith('#') and not line.startswith('BIP85:')]
        
        if not mnemonic_lines:
            print("❌ No mnemonic found in output")
            return False
            
        mnemonic = mnemonic_lines[0].strip()
        if len(mnemonic.split()) != 12:
            print(f"❌ BIP39 result invalid: got {len(mnemonic.split())} words, expected 12")
            print(f"   Mnemonic: {mnemonic}")
            return False
    
    print("✅ Basic functionality test passed")
    return True

def validate_test_suite():
    """Run the test suite."""
    print("🧪 Running test suite...")
    
    success, stdout, stderr = run_command(['python', '-m', 'pytest', 'tests/bip85/', '-q'])
    if not success:
        print(f"❌ Test suite failed: {stderr}")
        return False
    
    print("✅ Test suite passed")
    return True

def main():
    """Run validation."""
    print("🚀 BIP85 Release Validation")
    print("=" * 40)
    
    tests = [
        validate_basic_functionality,
        validate_test_suite
    ]
    
    all_passed = True
    for test in tests:
        if not test():
            all_passed = False
    
    print("=" * 40)
    if all_passed:
        print("🎉 All validations passed!")
        return 0
    else:
        print("❌ Some validations failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 