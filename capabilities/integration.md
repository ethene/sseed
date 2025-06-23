# Integration Capabilities

SSeed is designed for seamless integration into diverse environments and workflows. From simple pip installation to complex enterprise systems, SSeed provides flexible integration options while maintaining security and performance.

## Package Distribution and Installation

### PyPI Package Distribution
SSeed is distributed as a standard Python package with comprehensive metadata and dependencies.

#### Package Structure
```
sseed-0.1.0-py3-none-any.whl
├── sseed/                    # Main package
│   ├── __init__.py
│   ├── __main__.py          # Module entry point
│   ├── cli.py               # Command-line interface
│   ├── bip39.py             # BIP-39 implementation
│   ├── slip39_operations.py # SLIP-39 implementation
│   ├── entropy.py           # Entropy generation
│   ├── validation.py        # Input validation
│   ├── file_operations.py   # File I/O
│   ├── exceptions.py        # Custom exceptions
│   └── logging_config.py    # Logging configuration
└── metadata/                # Package metadata
    ├── METADATA             # Package information
    ├── entry_points.txt     # CLI entry points
    └── RECORD               # File manifest
```

#### Installation Methods

##### Standard Installation
```bash
# Install from PyPI
pip install sseed

# Install specific version
pip install sseed==0.1.0

# Install with development dependencies
pip install sseed[dev]
```

##### Advanced Installation Options
```bash
# Install from source
git clone <repository-url>
cd sseed
pip install .

# Editable development install
pip install -e .

# Install from wheel file
pip install sseed-0.1.0-py3-none-any.whl

# Install to specific location
pip install --target /custom/path sseed
```

##### Environment-Specific Installation
```bash
# Virtual environment
python -m venv sseed-env
source sseed-env/bin/activate
pip install sseed

# Conda environment
conda create -n sseed python=3.12
conda activate sseed
pip install sseed

# Docker container
FROM python:3.12-alpine
RUN pip install sseed
```

### Cross-Platform Compatibility

#### Platform Support Matrix
| Platform | Status | Notes |
|----------|--------|-------|
| **Linux** | ✅ Full Support | All distributions |
| **macOS** | ✅ Full Support | Intel and Apple Silicon |
| **Windows** | ✅ Full Support | Windows 10/11 |
| **FreeBSD** | ✅ Full Support | Via Python compatibility |
| **OpenBSD** | ✅ Full Support | Via Python compatibility |
| **WSL** | ✅ Full Support | Windows Subsystem for Linux |

#### Architecture Support
- **x86_64**: Full support on all platforms
- **ARM64**: Full support (Apple Silicon, ARM servers)
- **ARM32**: Compatible via Python (Raspberry Pi)
- **Other**: Any architecture supporting Python 3.10+

## Command-Line Integration

### Official Trezor CLI Compatibility

SSeed is fully compatible with the official Trezor `shamir` CLI tool from the [python-shamir-mnemonic](https://github.com/trezor/python-shamir-mnemonic) repository. Both tools use the same `shamir-mnemonic==0.3.0` library, ensuring perfect interoperability.

#### Compatibility Matrix
| **Create With** | **Recover With** | **Result** | **Output Format** |
|-----------------|------------------|------------|-------------------|
| `sseed shard` | `shamir recover` | ✅ **Works** | Raw entropy/master secret |
| `shamir create` | `sseed restore` | ✅ **Works** | BIP-39 mnemonic |
| `sseed shard` | `sseed restore` | ✅ **Works** | BIP-39 mnemonic |
| `shamir create` | `shamir recover` | ✅ **Works** | Raw entropy/master secret |

#### Installing the Official Trezor CLI
```bash
# Install official Trezor shamir CLI tool
pip install shamir-mnemonic[cli]

# Verify installation
shamir --help
```

#### Cross-Tool Usage Examples

**Create shards with sseed, recover with official Trezor CLI:**
```bash
# Generate BIP-39 mnemonic and create SLIP-39 shards
sseed gen -o mnemonic.txt
sseed shard -i mnemonic.txt -g 2-of-3 --separate -o shards

# Recover using official Trezor shamir tool (returns raw entropy)
shamir recover
# Enter shards interactively
# Output: Your master secret is: a1b2c3d4e5f6...
```

**Create shards with official Trezor CLI, recover with sseed:**
```bash
# Create SLIP-39 shards with official Trezor tool
shamir create 2of3
# Save the displayed shards to files: shard1.txt, shard2.txt

# Recover BIP-39 mnemonic using sseed
sseed restore shard1.txt shard2.txt
# Output: word1 word2 word3 ... (BIP-39 mnemonic)
```

#### Key Differences in Output

- **`shamir recover`**: Returns the raw entropy (master secret) as hexadecimal
  ```
  Your master secret is: d1f40a3284c9f822fcff899819ca1dd2
  ```

- **`sseed restore`**: Returns the reconstructed BIP-39 mnemonic phrase
  ```
  spin park million another panel badge view van object soft manual picture
  ```

Both outputs represent the same cryptographic material in different formats, ensuring full compatibility while serving different use cases.

### System Integration
SSeed integrates seamlessly with system command-line tools and shells.

#### Shell Integration
```bash
# Bash completion (if available)
complete -W "gen shard restore" sseed

# Zsh completion
autoload -U compinit && compinit
# Add sseed completions to fpath

# Fish completion
complete -c sseed -f -a "gen shard restore"
```

#### PATH Integration
```bash
# Verify installation
which sseed
# Output: /usr/local/bin/sseed

# Check version
sseed --version
# Output: sseed 0.1.0

# Module execution
python -m sseed --help
```

### Scripting Integration

#### Bash Scripts
```bash
#!/bin/bash
# Enterprise backup script

set -euo pipefail

BACKUP_DIR="/secure/backup/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Generate master seed
if ! sseed gen -o "$BACKUP_DIR/master.txt"; then
    echo "Error: Failed to generate master seed" >&2
    exit 1
fi

# Create distributed shards
sseed shard -i "$BACKUP_DIR/master.txt" -g 3-of-5 \
    --separate -o "$BACKUP_DIR/shard"

# Verify integrity
if sseed restore "$BACKUP_DIR"/shard_*.txt \
    -o "$BACKUP_DIR/verify.txt"; then
    echo "Backup created and verified successfully"
    rm "$BACKUP_DIR/verify.txt"
else
    echo "Error: Backup verification failed" >&2
    exit 1
fi
```

#### PowerShell Integration
```powershell
# Windows PowerShell script
$BackupDir = "C:\Secure\Backup\$(Get-Date -Format 'yyyyMMdd_HHmmss')"
New-Item -Path $BackupDir -ItemType Directory -Force

# Generate and shard
sseed gen -o "$BackupDir\master.txt"
sseed shard -i "$BackupDir\master.txt" -g 3-of-5 --separate -o "$BackupDir\shard"

# Verification
$verification = sseed restore "$BackupDir\shard_*.txt" -o "$BackupDir\verify.txt"
if ($LASTEXITCODE -eq 0) {
    Write-Host "Backup successful"
    Remove-Item "$BackupDir\verify.txt"
}
```

### Process Integration

#### Exit Code Handling
```bash
# Error handling with exit codes
if sseed gen -o seed.txt; then
    echo "Generation successful (exit code: $?)"
else
    case $? in
        1) echo "Usage or file error" >&2 ;;
        2) echo "Cryptographic error" >&2 ;;
        *) echo "Unknown error" >&2 ;;
    esac
    exit 1
fi
```

#### Signal Handling
```bash
# Graceful shutdown handling
trap 'echo "Interrupted"; rm -f temp_seed.txt; exit 130' INT TERM

sseed gen -o temp_seed.txt
# Process temp_seed.txt
rm temp_seed.txt
```

## Programmatic API Integration

### Python Module Integration
SSeed can be imported and used as a Python library for programmatic access.

#### Direct Module Usage
```python
import sseed
from sseed.bip39 import generate_mnemonic
from sseed.slip39_operations import create_shards, reconstruct_mnemonic
from sseed.validation import validate_mnemonic_checksum

# Generate BIP-39 mnemonic
mnemonic = generate_mnemonic()
print(f"Generated: {mnemonic}")

# Validate mnemonic
is_valid = validate_mnemonic_checksum(mnemonic.split())
print(f"Valid: {is_valid}")

# Create SLIP-39 shards
shards = create_shards(mnemonic, "3-of-5")
print(f"Created {len(shards)} shards")

# Reconstruct from shards
reconstructed = reconstruct_mnemonic(shards[:3])
print(f"Reconstructed: {reconstructed}")
```

#### CLI Module Integration
```python
import subprocess
import json

# Execute CLI commands programmatically
def generate_seed():
    """Generate seed using CLI."""
    result = subprocess.run(
        ['sseed', 'gen'],
        capture_output=True,
        text=True,
        check=True
    )
    return result.stdout.strip()

def create_shards_cli(mnemonic, config):
    """Create shards using CLI."""
    result = subprocess.run(
        ['sseed', 'shard', '-g', config],
        input=mnemonic,
        capture_output=True,
        text=True,
        check=True
    )
    return result.stdout.strip().split('\n')

# Usage
seed = generate_seed()
shards = create_shards_cli(seed, '3-of-5')
```

### API Wrapper Development
```python
class SSeedAPI:
    """High-level API wrapper for SSeed operations."""
    
    def __init__(self, secure_cleanup=True):
        self.secure_cleanup = secure_cleanup
    
    def generate_wallet_backup(self, threshold_config="3-of-5"):
        """Generate complete wallet backup with shards."""
        # Generate master seed
        master = generate_mnemonic()
        
        # Create shards
        shards = create_shards(master, threshold_config)
        
        # Return structured result
        result = {
            'master_seed': master,
            'shards': shards,
            'config': threshold_config,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        if self.secure_cleanup:
            # Secure cleanup implementation
            pass
            
        return result
    
    def restore_wallet(self, shard_list):
        """Restore wallet from shard list."""
        return reconstruct_mnemonic(shard_list)
```

## System Integration Patterns

### Configuration Management

#### Environment Variables
```bash
# Configuration via environment
export SSEED_LOG_LEVEL=INFO
export SSEED_OUTPUT_DIR=/secure/seeds
export SSEED_DEFAULT_GROUP=3-of-5

# Use in scripts
sseed gen -o "${SSEED_OUTPUT_DIR}/seed_$(date +%s).txt"
```

#### Configuration Files
```python
# config.py - Application configuration
SSEED_CONFIG = {
    'default_group': '3-of-5',
    'output_directory': '/secure/backup',
    'log_level': 'INFO',
    'secure_cleanup': True
}

# Usage in application
from config import SSEED_CONFIG
import subprocess

subprocess.run([
    'sseed', 'shard', 
    '-g', SSEED_CONFIG['default_group'],
    '-o', f"{SSEED_CONFIG['output_directory']}/shards.txt"
])
```

### Monitoring and Observability

#### Logging Integration
```python
import logging
import subprocess

# Configure application logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('wallet_manager')

def secure_generate():
    """Generate seed with monitoring."""
    logger.info("Starting secure seed generation")
    
    try:
        result = subprocess.run(
            ['sseed', 'gen'],
            capture_output=True,
            text=True,
            check=True
        )
        logger.info("Seed generation completed successfully")
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        logger.error(f"Seed generation failed: {e}")
        raise
```

#### Metrics Collection
```python
import time
import psutil
from dataclasses import dataclass

@dataclass
class OperationMetrics:
    operation: str
    duration_ms: float
    memory_mb: float
    success: bool

def measure_sseed_operation(command_args):
    """Measure SSeed operation performance."""
    start_time = time.time()
    start_memory = psutil.Process().memory_info().rss / 1024 / 1024
    
    try:
        result = subprocess.run(
            ['sseed'] + command_args,
            capture_output=True,
            text=True,
            check=True
        )
        success = True
    except subprocess.CalledProcessError:
        success = False
    
    end_time = time.time()
    end_memory = psutil.Process().memory_info().rss / 1024 / 1024
    
    return OperationMetrics(
        operation=' '.join(command_args),
        duration_ms=(end_time - start_time) * 1000,
        memory_mb=end_memory - start_memory,
        success=success
    )
```

## Enterprise Integration

### Docker Integration

#### Production Dockerfile
```dockerfile
FROM python:3.12-alpine AS builder

# Install build dependencies
RUN apk add --no-cache gcc musl-dev

# Install SSeed
RUN pip install --no-cache-dir sseed

FROM python:3.12-alpine AS runtime

# Copy installed packages
COPY --from=builder /usr/local/lib/python3.12/site-packages/ \
     /usr/local/lib/python3.12/site-packages/
COPY --from=builder /usr/local/bin/sseed /usr/local/bin/

# Create non-root user
RUN adduser -D -s /bin/sh sseed

# Security hardening
RUN chmod 755 /usr/local/bin/sseed && \
    chown root:root /usr/local/bin/sseed

USER sseed
WORKDIR /app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s \
    CMD sseed --help > /dev/null || exit 1

ENTRYPOINT ["sseed"]
```

#### Docker Compose
```yaml
version: '3.8'
services:
  sseed:
    image: sseed:latest
    volumes:
      - ./output:/app/output:rw
      - ./config:/app/config:ro
    environment:
      - SSEED_LOG_LEVEL=INFO
    security_opt:
      - no-new-privileges:true
    read_only: true
    tmpfs:
      - /tmp:size=10M,mode=1777
    networks:
      - isolated
    restart: unless-stopped

networks:
  isolated:
    driver: bridge
    internal: true
```

### Kubernetes Integration

#### Pod Specification
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: sseed-worker
  labels:
    app: sseed
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    fsGroup: 1000
  containers:
  - name: sseed
    image: sseed:latest
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop:
        - ALL
    resources:
      requests:
        memory: "64Mi"
        cpu: "50m"
      limits:
        memory: "128Mi"
        cpu: "100m"
    volumeMounts:
    - name: output
      mountPath: /app/output
    - name: tmp
      mountPath: /tmp
  volumes:
  - name: output
    persistentVolumeClaim:
      claimName: sseed-output
  - name: tmp
    emptyDir:
      sizeLimit: 10Mi
```

### CI/CD Integration

#### GitHub Actions
```yaml
name: Secure Seed Management
on:
  workflow_dispatch:
    inputs:
      operation:
        description: 'Operation to perform'
        required: true
        type: choice
        options:
        - generate
        - shard
        - verify

jobs:
  secure-operation:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.12'
    
    - name: Install SSeed
      run: pip install sseed
    
    - name: Perform Operation
      run: |
        case "${{ github.event.inputs.operation }}" in
          generate)
            sseed gen -o seeds/new_seed.txt
            ;;
          shard)
            sseed shard -i seeds/master.txt -g 3-of-5 -o seeds/shards.txt
            ;;
          verify)
            sseed restore seeds/shard_*.txt -o seeds/verify.txt
            ;;
        esac
    
    - name: Upload Artifacts
      uses: actions/upload-artifact@v3
      with:
        name: secure-seeds
        path: seeds/
        retention-days: 1
```

#### Jenkins Pipeline
```groovy
pipeline {
    agent any
    
    environment {
        SSEED_LOG_LEVEL = 'INFO'
        VAULT_PATH = '/secure/vault'
    }
    
    stages {
        stage('Setup') {
            steps {
                sh 'pip install sseed'
            }
        }
        
        stage('Generate Backup') {
            steps {
                script {
                    sh """
                        mkdir -p ${VAULT_PATH}
                        sseed gen -o ${VAULT_PATH}/master_\${BUILD_NUMBER}.txt
                        sseed shard -i ${VAULT_PATH}/master_\${BUILD_NUMBER}.txt \\
                            -g 3-of-5 --separate -o ${VAULT_PATH}/shard_\${BUILD_NUMBER}
                    """
                }
            }
        }
        
        stage('Verify') {
            steps {
                sh """
                    sseed restore ${VAULT_PATH}/shard_\${BUILD_NUMBER}_*.txt \\
                        -o ${VAULT_PATH}/verify_\${BUILD_NUMBER}.txt
                """
            }
        }
        
        stage('Cleanup') {
            steps {
                sh "rm -f ${VAULT_PATH}/verify_\${BUILD_NUMBER}.txt"
            }
        }
    }
    
    post {
        always {
            archiveArtifacts artifacts: 'vault/**', fingerprint: true
        }
    }
}
```

## Third-Party Integration

### Vault Systems Integration

#### HashiCorp Vault
```bash
#!/bin/bash
# Integrate with HashiCorp Vault

# Generate seed
SEED=$(sseed gen)

# Store in Vault
vault kv put secret/wallet/master value="$SEED"

# Create shards
SHARDS=$(echo "$SEED" | sseed shard -g 3-of-5)

# Store shards separately
echo "$SHARDS" | while IFS= read -r shard; do
    INDEX=$((INDEX + 1))
    vault kv put "secret/wallet/shard$INDEX" value="$shard"
done
```

#### AWS Secrets Manager
```python
import boto3
import subprocess

def store_seed_in_aws(region='us-east-1'):
    """Store generated seed in AWS Secrets Manager."""
    client = boto3.client('secretsmanager', region_name=region)
    
    # Generate seed
    result = subprocess.run(
        ['sseed', 'gen'],
        capture_output=True,
        text=True,
        check=True
    )
    seed = result.stdout.strip()
    
    # Store in AWS
    response = client.create_secret(
        Name='wallet/master-seed',
        SecretString=seed,
        Description='Generated BIP-39 master seed'
    )
    
    return response['ARN']
```

### Backup System Integration

#### Automated Backup
```python
import shutil
import os
from datetime import datetime

class SecureBackupManager:
    def __init__(self, backup_root='/secure/backups'):
        self.backup_root = backup_root
        
    def create_distributed_backup(self, identifier=None):
        """Create distributed backup with geographic distribution."""
        if not identifier:
            identifier = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            
        # Create backup directory
        backup_dir = os.path.join(self.backup_root, identifier)
        os.makedirs(backup_dir, exist_ok=True)
        
        # Generate master seed
        master_file = os.path.join(backup_dir, 'master.txt')
        subprocess.run(['sseed', 'gen', '-o', master_file], check=True)
        
        # Create 3-of-5 shards
        subprocess.run([
            'sseed', 'shard', 
            '-i', master_file,
            '-g', '3-of-5',
            '--separate',
            '-o', os.path.join(backup_dir, 'shard')
        ], check=True)
        
        # Distribute shards to different locations
        shard_files = [f for f in os.listdir(backup_dir) if f.startswith('shard_')]
        locations = ['/backup/location1', '/backup/location2', '/backup/location3']
        
        for i, shard_file in enumerate(shard_files[:3]):
            dest_dir = locations[i % len(locations)]
            os.makedirs(dest_dir, exist_ok=True)
            shutil.copy2(
                os.path.join(backup_dir, shard_file),
                os.path.join(dest_dir, f'{identifier}_{shard_file}')
            )
        
        return backup_dir
```

## Performance Integration

### Caching Strategies
```python
import functools
import hashlib

class SSeedCache:
    """Simple caching for non-sensitive operations."""
    
    def __init__(self):
        self._cache = {}
    
    def cached_validation(self, mnemonic):
        """Cache validation results (non-sensitive)."""
        # Create hash of mnemonic for cache key
        cache_key = hashlib.sha256(mnemonic.encode()).hexdigest()
        
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Perform validation
        result = subprocess.run(
            ['sseed', 'shard', '-g', '1-of-1'],
            input=mnemonic,
            capture_output=True,
            text=True
        )
        
        is_valid = result.returncode == 0
        self._cache[cache_key] = is_valid
        return is_valid
```

### Batch Processing
```python
import concurrent.futures
import threading

class BatchSSeedProcessor:
    """Batch processing for high-volume operations."""
    
    def __init__(self, max_workers=4):
        self.max_workers = max_workers
        self._lock = threading.Lock()
    
    def generate_multiple_seeds(self, count):
        """Generate multiple seeds in parallel."""
        def generate_single():
            result = subprocess.run(
                ['sseed', 'gen'],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(generate_single) for _ in range(count)]
            seeds = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        return seeds
    
    def process_shard_batch(self, mnemonics, config='3-of-5'):
        """Process multiple mnemonics into shards."""
        def shard_single(mnemonic):
            result = subprocess.run(
                ['sseed', 'shard', '-g', config],
                input=mnemonic,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip().split('\n')
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(shard_single, m): m for m in mnemonics}
            results = {}
            
            for future in concurrent.futures.as_completed(futures):
                mnemonic = futures[future]
                results[mnemonic] = future.result()
        
        return results
```

SSeed's comprehensive integration capabilities enable deployment in any environment while maintaining security, performance, and operational simplicity. 