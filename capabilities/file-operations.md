# File Operations

SSeed provides robust file operation capabilities designed for security, reliability, and cross-platform compatibility. All file operations are optimized for performance while maintaining strict security standards.

## Input/Output Architecture

### Design Principles
- **Security First**: Path validation and sanitization
- **Cross-Platform**: Works on Windows, macOS, Linux
- **Unicode Support**: Full UTF-8 compatibility
- **Error Resilience**: Graceful error handling and recovery
- **Performance**: Optimized for small file operations

### I/O Patterns
SSeed supports multiple input/output patterns to accommodate different workflows:

```
Input Sources:
├── Standard Input (stdin)
├── File Input (-i flag)
├── Command Line Arguments
└── Here Documents

Output Destinations:
├── Standard Output (stdout) 
├── File Output (-o flag)
├── Separate Files (--separate)
└── Piped Output
```

## Input Handling

### Standard Input (stdin)
SSeed can read from standard input for seamless integration with Unix pipelines.

#### Mnemonic Input
```bash
# Pipe mnemonic for sharding
echo "abandon ability able about above absent absorb abstract absurd abuse access accident account accuse achieve acid acoustic acquire across act action actor actress actual" | sseed shard -g 3-of-5

# Here document input
sseed shard -g 3-of-5 << EOF
abandon ability able about above absent absorb abstract absurd abuse access accident
account accuse achieve acid acoustic acquire across act action actor actress actual
EOF

# File redirection
sseed shard -g 3-of-5 < mnemonic.txt
```

#### Shard Input for Restoration
```bash
# Multiple shards via stdin
cat shards.txt | sseed restore

# Pipe multiple files
cat shard1.txt shard2.txt shard3.txt | sseed restore

# Process substitution
sseed restore < <(cat shard*.txt)
```

### File Input
Direct file input with comprehensive validation and error handling.

#### Basic File Input
```bash
# Read mnemonic from file
sseed shard -i seed.txt -g 3-of-5

# Process multiple files
for file in seeds/*.txt; do
    sseed shard -i "$file" -g 3-of-5 -o "shards/$(basename "$file" .txt)_shards.txt"
done
```

#### File Validation
SSeed performs comprehensive validation on input files:

```python
def validate_input_file(file_path: str) -> None:
    """Comprehensive input file validation."""
    
    # Path security validation
    if '..' in file_path or file_path.startswith('/'):
        raise FileError("Potentially unsafe file path")
    
    # Existence check
    if not os.path.exists(file_path):
        raise FileError(f"File not found: {file_path}")
    
    # Permissions check
    if not os.access(file_path, os.R_OK):
        raise FileError(f"File not readable: {file_path}")
    
    # Size validation (prevent DoS)
    file_size = os.path.getsize(file_path)
    if file_size > MAX_INPUT_SIZE:  # 1MB limit
        raise FileError(f"File too large: {file_size} bytes")
    
    # Content validation
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                raise FileError("File is empty")
    except UnicodeDecodeError:
        raise FileError("File contains invalid UTF-8")
```

### Input Format Support

#### Flexible Whitespace Handling
```python
def parse_mnemonic_input(content: str) -> List[str]:
    """Parse mnemonic with flexible whitespace handling."""
    
    # Normalize whitespace
    content = re.sub(r'\s+', ' ', content.strip())
    
    # Split into words
    words = content.split()
    
    # Remove empty strings
    words = [word for word in words if word]
    
    return words
```

#### Comment Line Support
SSeed ignores comment lines starting with `#` for better file organization:

```
# BIP-39 Mnemonic - Generated 2024-06-19
# Purpose: Master wallet seed
# Group: Personal backup
#
abandon ability able about above absent absorb abstract absurd abuse access accident
account accuse achieve acid acoustic acquire across act action actor actress actual
```

#### Multi-Line Support
```
# Multi-line mnemonic format
abandon ability able about above absent
absorb abstract absurd abuse access accident
account accuse achieve acid acoustic acquire
across act action actor actress actual
```

## Output Handling

### Standard Output (stdout)
Default output destination for easy integration with other tools.

#### Single Output
```bash
# Generate to stdout
sseed gen
# Output: abandon ability able about above absent absorb abstract absurd abuse access accident account accuse achieve acid acoustic acquire across act action actor actress actual

# Shard to stdout
sseed shard -i seed.txt -g 3-of-5
# Output: Multiple shards with headers
```

#### Piped Output
```bash
# Count words in generated mnemonic
sseed gen | wc -w
# Output: 24

# Encrypt output
sseed gen | gpg --encrypt --armor > encrypted_seed.asc

# Process shards
sseed shard -i seed.txt -g 3-of-5 | while IFS= read -r shard; do
    echo "Processing: $shard"
done
```

### File Output
Structured file output with security and organization features.

#### Single File Output
```bash
# Generate to file
sseed gen -o master_seed.txt

# Shard to file
sseed shard -i seed.txt -g 3-of-5 -o shards.txt

# Restore to file
sseed restore shard*.txt -o recovered.txt
```

#### Separate File Output
```bash
# Create separate files for each shard
sseed shard -i seed.txt -g 3-of-5 --separate -o backup_shards

# Creates:
# backup_shards_01.txt
# backup_shards_02.txt  
# backup_shards_03.txt
# backup_shards_04.txt
# backup_shards_05.txt
```

### Output Format and Structure

#### Shard File Format
```
# SLIP-39 Shard
# Generated by sseed on 2024-06-19 14:30:15
# Group 1, Shard 1 of 5 (threshold: 3)
# Configuration: 3-of-5
#
academic acid acrobat romp charity artwork donor voting declare
```

#### Multi-Shard File Format
```
# SLIP-39 Shards - 3-of-5 Configuration
# Generated by sseed on 2024-06-19 14:30:15
# Total shards: 5, Threshold: 3
#

# Group 1, Shard 1 of 5
academic acid acrobat romp charity artwork donor voting declare

# Group 1, Shard 2 of 5
academic acid beard romp dwarf slice harvest bold enough

# Group 1, Shard 3 of 5
academic acid ceramic romp echo tactics identify sister busy
```

## File Security Features

### Path Sanitization
SSeed sanitizes file paths to prevent security vulnerabilities:

```python
def sanitize_file_path(path: str) -> str:
    """Sanitize file path for security."""
    
    # Remove potentially dangerous characters
    path = re.sub(r'[^\w\-_./]', '_', path)
    
    # Prevent directory traversal
    path = path.replace('..', '_')
    path = path.replace('//', '/')
    
    # Handle absolute paths (make relative)
    if path.startswith('/'):
        path = '_' + path.replace('/', '_')
    
    return path
```

### File Permission Management
```python
def create_secure_file(file_path: str, content: str) -> None:
    """Create file with secure permissions."""
    
    # Create file with restrictive permissions (600)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    # Set secure permissions (owner read/write only)
    os.chmod(file_path, 0o600)
```

### Atomic File Operations
```python
def atomic_write(file_path: str, content: str) -> None:
    """Atomic file write to prevent partial writes."""
    
    temp_path = f"{file_path}.tmp"
    
    try:
        # Write to temporary file
        with open(temp_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Atomic move
        os.rename(temp_path, file_path)
    
    except Exception:
        # Clean up on failure
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise
```

## Unicode and Encoding Support

### UTF-8 Standard
All file operations use UTF-8 encoding with proper error handling:

```python
def read_file_utf8(file_path: str) -> str:
    """Read file with UTF-8 encoding and error handling."""
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    except UnicodeDecodeError as e:
        raise FileError(f"Invalid UTF-8 encoding in {file_path}: {e}")
    
    except IOError as e:
        raise FileError(f"Cannot read file {file_path}: {e}")
```

### Unicode Normalization
SSeed applies NFKD normalization for consistent mnemonic handling:

```python
import unicodedata

def normalize_mnemonic(text: str) -> str:
    """Apply NFKD normalization to mnemonic text."""
    
    # NFKD normalization as per BIP-39
    normalized = unicodedata.normalize('NFKD', text)
    
    # Remove control characters
    cleaned = ''.join(char for char in normalized 
                     if unicodedata.category(char) != 'Cc')
    
    return cleaned
```

### Character Encoding Validation
```python
def validate_character_encoding(text: str) -> None:
    """Validate character encoding for mnemonic compatibility."""
    
    # Check for valid ASCII characters in words
    words = text.split()
    
    for word in words:
        # BIP-39 words are ASCII only
        try:
            word.encode('ascii')
        except UnicodeEncodeError:
            raise ValidationError(f"Non-ASCII characters in word: {word}")
        
        # Check for valid characters
        if not re.match(r'^[a-z]+$', word):
            raise ValidationError(f"Invalid characters in word: {word}")
```

## Cross-Platform Compatibility

### Path Handling
SSeed handles path differences across operating systems:

```python
import os
import pathlib

def normalize_path(path: str) -> str:
    """Normalize path for cross-platform compatibility."""
    
    # Use pathlib for cross-platform path handling
    normalized = pathlib.Path(path).resolve()
    
    return str(normalized)

def ensure_directory(dir_path: str) -> None:
    """Ensure directory exists across platforms."""
    
    path_obj = pathlib.Path(dir_path)
    path_obj.mkdir(parents=True, exist_ok=True)
```

### Line Ending Handling
```python
def write_cross_platform(file_path: str, content: str) -> None:
    """Write file with appropriate line endings."""
    
    # Use universal newlines
    with open(file_path, 'w', encoding='utf-8', newline='') as f:
        # Normalize to Unix line endings
        content = content.replace('\r\n', '\n').replace('\r', '\n')
        f.write(content)
```

### File System Limitations
```python
def validate_filename(filename: str) -> str:
    """Validate filename for cross-platform compatibility."""
    
    # Reserved names on Windows
    reserved_names = {
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    }
    
    # Check reserved names
    base_name = os.path.splitext(filename)[0].upper()
    if base_name in reserved_names:
        filename = f"_{filename}"
    
    # Remove invalid characters
    invalid_chars = r'<>:"/\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Length limits
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:255-len(ext)] + ext
    
    return filename
```

## Performance Optimization

### Buffered I/O
```python
def read_large_file(file_path: str, chunk_size: int = 8192) -> str:
    """Read large file with buffering."""
    
    content = []
    
    with open(file_path, 'r', encoding='utf-8', buffering=chunk_size) as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            content.append(chunk)
    
    return ''.join(content)
```

### Memory-Efficient Processing
```python
def process_file_streaming(file_path: str) -> Iterator[str]:
    """Process file line by line for memory efficiency."""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            # Skip comments and empty lines
            line = line.strip()
            if line and not line.startswith('#'):
                yield line
```

### File Caching
```python
class FileCache:
    """Simple file content cache for performance."""
    
    def __init__(self, max_size: int = 100):
        self.cache = {}
        self.max_size = max_size
        self.access_order = []
    
    def get_file_content(self, file_path: str) -> str:
        """Get file content with caching."""
        
        # Check cache
        if file_path in self.cache:
            # Update access order
            self.access_order.remove(file_path)
            self.access_order.append(file_path)
            return self.cache[file_path]
        
        # Read file
        content = read_file_utf8(file_path)
        
        # Add to cache
        self.cache[file_path] = content
        self.access_order.append(file_path)
        
        # Evict if necessary
        if len(self.cache) > self.max_size:
            oldest = self.access_order.pop(0)
            del self.cache[oldest]
        
        return content
```

## Error Handling and Recovery

### File Operation Errors
```python
class FileOperationError(Exception):
    """Base class for file operation errors."""
    pass

class FileNotFoundError(FileOperationError):
    """File not found error."""
    pass

class PermissionError(FileOperationError):
    """File permission error."""
    pass

class EncodingError(FileOperationError):
    """File encoding error."""
    pass

def safe_file_operation(operation, *args, **kwargs):
    """Wrapper for safe file operations with error handling."""
    
    try:
        return operation(*args, **kwargs)
    
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise FileOperationError(f"File not found: {e}")
    
    except PermissionError as e:
        logger.error(f"Permission denied: {e}")
        raise FileOperationError(f"Permission denied: {e}")
    
    except UnicodeDecodeError as e:
        logger.error(f"Encoding error: {e}")
        raise EncodingError(f"Invalid file encoding: {e}")
    
    except IOError as e:
        logger.error(f"I/O error: {e}")
        raise FileOperationError(f"I/O error: {e}")
```

### Recovery Strategies
```python
def resilient_file_write(file_path: str, content: str, max_retries: int = 3) -> None:
    """Write file with retry logic."""
    
    for attempt in range(max_retries):
        try:
            atomic_write(file_path, content)
            return
        
        except IOError as e:
            logger.warning(f"Write attempt {attempt + 1} failed: {e}")
            
            if attempt == max_retries - 1:
                raise FileOperationError(f"Failed to write after {max_retries} attempts")
            
            # Brief delay before retry
            time.sleep(0.1 * (attempt + 1))
```

## File Format Specifications

### Mnemonic File Format
```
# Specification: BIP-39 mnemonic file
# Encoding: UTF-8
# Line endings: Unix (LF) or Windows (CRLF)
# Comments: Lines starting with #

# Example mnemonic file
# Generated: 2024-06-19 14:30:15
# Purpose: Master wallet seed
#
abandon ability able about above absent absorb abstract absurd abuse access accident
account accuse achieve acid acoustic acquire across act action actor actress actual
```

### Shard File Format
```
# Specification: SLIP-39 shard file
# Encoding: UTF-8
# Line endings: Unix (LF) or Windows (CRLF)
# Comments: Lines starting with #

# SLIP-39 Shard
# Generated by sseed on 2024-06-19 14:30:15
# Group 1, Shard 1 of 5 (threshold: 3)
# Configuration: 3-of-5
#
academic acid acrobat romp charity artwork donor voting declare
```

### Multi-Shard File Format
```
# Specification: Multiple SLIP-39 shards in one file
# Encoding: UTF-8
# Separation: Blank lines between shards
# Headers: Comment headers for each shard

# SLIP-39 Shards - 3-of-5 Configuration
# Generated by sseed on 2024-06-19 14:30:15

# Shard 1
academic acid acrobat romp charity artwork donor voting declare

# Shard 2  
academic acid beard romp dwarf slice harvest bold enough

# Shard 3
academic acid ceramic romp echo tactics identify sister busy
```

SSeed's file operations provide a robust, secure, and cross-platform foundation for all mnemonic and shard management activities while maintaining simplicity and performance. 