# SA Framework

A Python framework for working with semantic objects and query languages.

## 🚀 Quick Start (For Users)

### Install the SA Shell

The easiest way to get started is with our pre-built shell:

**For macOS:**
```bash
# Download and run the installer
curl -L -o sa-installer https://zubatomic.com/sa-installer
chmod +x sa-installer
./sa-installer
```

**For Alma Linux (x86_64):**
```bash
# Download and run the installer
curl -L -o sa-installer https://zubatomic.com/sa-installer-alma
chmod +x sa-installer
./sa-installer
```

This will:
- Download the latest SA Shell
- Install it to `~/.local/bin`
- Add it to your PATH
- Run a test to ensure everything works

### Use the SA Shell

```bash
# Start interactive shell
sa-shell

# Run a single query
sa-shell -q ".count()"

# Run with verbose output
sa-shell -v ".filter(.equals(.get_field('name'), 'John'))"

# Show help
sa-shell --help
```

**Performance**: First run takes ~25 seconds (download + install), subsequent runs are **0.5-1.2 seconds**!

## Installation

### From source
```bash
git clone <your-repo-url>
cd sa
pip install -e .
```

### Development installation
```bash
pip install -e ".[dev]"
```

## Usage

```python
# Import from the main sa package
from sa import SAObject, ObjectList

# Or import from specific submodules
from sa.core.sa_object import SAObject
from sa.query_language.main import ObjectList

# Create a semantic object
obj_data = {
    "__types__": ["person", "employee"],
    "__id__": "12345",
    "__source__": "hr_database"
}

obj = SAObject(obj_data)

# Access object properties
print(obj.types)    # ['person', 'employee']
print(obj.id)       # '12345'
print(obj.source)   # 'hr_database'
```

## Running the Shell

The SA Query Language Shell provides an interactive interface:

```bash
# Option 1: Use the entry point script
./sa-shell

# Option 2: Run directly with Python
python -m sa.shell.shell

# Option 3: Import and run programmatically
from sa import shell_main
shell_main()
```

## Project Structure

```
sa/
├── sa/                     # Main package
│   ├── __init__.py        # Main package entry point
│   ├── core/              # Core functionality
│   │   ├── __init__.py
│   │   └── sa_object.py   # Base SAObject class
│   ├── query_language/    # Query language functionality
│   │   ├── __init__.py
│   │   └── main.py        # ObjectList and query features
│   └── shell/             # Interactive shell
│       ├── __init__.py
│       └── shell.py       # Shell implementation
├── sa-shell               # Shell entry point script
├── providers.txt          # Provider endpoints configuration
├── setup.py               # Package configuration
├── pyproject.toml         # Modern Python packaging
├── requirements.txt       # Dependencies
└── README.md             # This file
```

## Configuration

The shell automatically loads provider endpoints from `~/.sa/saps.txt` at startup. Each line should contain a URL endpoint:

```
https://api.example.com/v1/search
https://data.provider.com/query
http://localhost:8080/api
```

Lines starting with `#` are treated as comments and ignored.

The file will be created automatically if it doesn't exist.

## 🛠️ Development

### Running tests
```bash
pytest
```

### Code formatting
```bash
black .
```

### Linting
```bash
flake8
```

### Type checking
```bash
mypy .
```

## 🔍 Performance Profiling & Investigation

The SA framework includes built-in profiling capabilities to help identify performance bottlenecks and optimize query execution.

### Enabling Profiling

#### Command Line Profiling
```bash
# Run a single query with profiling
python -m sa.shell.shell --print-profiling-information "person.count()"

# Run with debug output for detailed investigation
python -m sa.shell.shell --debug "lol[.best_friend.salary == 85000].count()"
```

#### Interactive Shell Profiling
```bash
# Start interactive shell
python -m sa.shell.shell

# Enable profiling mode
profile

# Run your queries (profiling will be shown)
person.count()
lol[.best_friend.salary == 85000].count()

# Disable profiling
profile
```

### Understanding Profiling Output

The profiling system provides hierarchical timing information:

```
⏱️  Profiling Summary:
   Total time: 199.1μs

   filter (22.9μs)
     -> get_field: 100006 executions, avg 4.7μs, total 465.9ms
   get_field: 100006 operations, avg 4.7μs, total 465.9ms
   Chain(1 ops): 200013 operations, avg 15.3μs, total 3.065s
   Total query execution: 1 operations, avg 1.700s, total 1.700s
```

**Key Metrics:**
- **Total time**: Overall query execution time
- **Operation timing**: Individual operation duration and frequency
- **Hierarchical breakdown**: Shows parent-child relationships between operations
- **Execution counts**: How many times each operation was called

### Performance Optimization Features

The SA framework includes several automatic optimizations:

#### 1. Type Filtering Optimization
- **Fast path**: `person.count()` uses pre-computed type index
- **Speedup**: ~15x faster than naive filtering
- **Detection**: Automatically detects `.__types__.includes('type_name')` patterns

#### 2. ID Filtering Optimization  
- **Fast path**: `#obj_A` uses pre-computed ID index
- **Speedup**: ~45,000x faster than regex matching
- **Detection**: Automatically detects `.__id__ =~ '^id$'` patterns

#### 3. Complex Filter Optimization
- **Pre-filtering**: Detects type filters at start of complex chains
- **Example**: `lol[.best_friend.salary == 85000]` pre-filters by type first
- **Benefit**: Reduces context size before applying complex filters

### Profiling Investigation Workflow

#### 1. Identify Slow Queries
```bash
# Test basic performance
python -m sa.shell.shell --print-profiling-information "person.count()"
python -m sa.shell.shell --print-profiling-information "lol.count()"
python -m sa.shell.shell --print-profiling-information "#obj_A"
```

#### 2. Analyze Complex Queries
```bash
# Test complex filtering
python -m sa.shell.shell --print-profiling-information "lol[.best_friend.salary == 85000].count()"

# Test with debug for detailed breakdown
python -m sa.shell.shell --debug "lol[.best_friend.salary == 85000].count()" 2>&1 | head -20
```

#### 3. Compare Performance
```bash
# Before optimization (if applicable)
python -m sa.shell.shell --print-profiling-information "slow_query"

# After optimization
python -m sa.shell.shell --print-profiling-information "optimized_query"
```

### Common Performance Patterns

#### Fast Queries (< 1ms)
- Simple type filtering: `person.count()`
- Simple ID filtering: `#obj_A`
- Basic field access: `person[0].name`

#### Medium Queries (1ms - 100ms)
- Complex type filtering: `person[.department == 'Engineering'].count()`
- Multiple field access: `person[0].best_friend.salary`

#### Slow Queries (> 100ms)
- Large dataset filtering: `lol[.best_friend.salary == 85000].count()`
- Complex nested operations: `person[.equals(.get_field('name'), 'John')].count()`

### Debugging Performance Issues

#### 1. Check if Fast Path is Used
```bash
python -m sa.shell.shell --debug "person.count()" 2>&1 | grep -E "(fast path|using fast)"
```

#### 2. Identify Bottlenecks
Look for operations with:
- High execution counts (> 10,000)
- Long average times (> 1ms)
- High total times (> 100ms)

#### 3. Profile Individual Components
```bash
# Test just the type filter
python -m sa.shell.shell --print-profiling-information "person"

# Test just the complex filter
python -m sa.shell.shell --print-profiling-information "lol[.best_friend.salary == 85000]"
```

### Performance Optimization Guidelines

#### For LLM Context & Future Development

1. **Always profile before optimizing** - Use `--print-profiling-information` to establish baseline
2. **Look for patterns** - Identify common slow operations across different queries
3. **Test edge cases** - Profile with different dataset sizes and query complexities
4. **Document findings** - Record performance improvements and optimization strategies
5. **Consider pre-computation** - Static indexes are built once and reused for consistent performance

#### Optimization Strategies

1. **Index-based filtering** - Pre-compute type and ID indexes for O(1) lookups
2. **Query rewriting** - Detect and optimize common query patterns
3. **Lazy evaluation** - Only process data when needed
4. **Caching** - Store frequently accessed computed values
5. **Parallel processing** - Process multiple objects simultaneously for large datasets

### Example Profiling Session

```bash
# 1. Test basic performance
$ python -m sa.shell.shell --print-profiling-information "person.count()"
⏱️  Profiling Summary:
   Total time: 207.9μs
   filter (23.1μs)
   count (20.0μs)
100004

# 2. Test complex query
$ python -m sa.shell.shell --print-profiling-information "lol[.best_friend.salary == 85000].count()"
⏱️  Profiling Summary:
   Total time: 110.204s
   filter (36.731s)
   count (24.1μs)
100000

# 3. Investigate with debug
$ python -m sa.shell.shell --debug "lol[.best_friend.salary == 85000].count()" 2>&1 | head -10
[filter operator runner] starting filter operation
[filter operator runner] context has 100008 objects
[filter operator runner] detected type filter at start of complex chain, pre-filtering by type: lol
```

This profiling system helps identify performance bottlenecks and guides optimization efforts for better query performance.

## 📦 Distribution & Deployment

### Building and Uploading New Versions

#### macOS Build

To release a new version of the SA Shell for macOS:

1. **Ensure you have access to zubatomic.com** (SSH key configured)

2. **Run the build and upload script**:
   ```bash
   ./build_and_upload.sh
   ```

   This script will:
   - Build the installer binary (`sa-installer`) using PyInstaller `--onefile`
   - Build the shell binary (`sa-shell-fast`) using PyInstaller `--onedir`
   - Create a distribution package (`sa-shell-0.1.0.zip`)
   - Upload both files to zubatomic.com via SCP

3. **Files uploaded**:
   - `zubatomic.com/sa.zip` ← Distribution package
   - `zubatomic.com/sa-installer` ← Installer binary

#### Alma Linux Build

To release a new version of the SA Shell for Alma Linux (x86_64):

1. **Ensure you have access to zubatomic.com** (SSH key configured)

2. **Run the Alma Linux build script**:
   ```bash
   ./build_alma.sh
   ```

   This script will:
   - Copy source files to zubatomic.com (x86_64 Debian server)
   - Install Python 3.9 and PyInstaller on the remote server
   - Build the installer binary (`sa-installer`) using PyInstaller `--onefile`
   - Build the shell binary (`sa-shell-fast`) using PyInstaller `--onedir`
   - Create a distribution package (`sa-shell-0.1.0-alma.tar.gz`)
   - Download and upload both files to zubatomic.com

3. **Files uploaded**:
   - `zubatomic.com/sa-alma.tar.gz` ← Distribution package
   - `zubatomic.com/sa-installer-alma` ← Installer binary

4. **Users can then install**:
   ```bash
   # macOS
   curl -L -o sa-installer https://zubatomic.com/sa-installer
   chmod +x sa-installer && ./sa-installer
   
   # Alma Linux
   curl -L -o sa-installer https://zubatomic.com/sa-installer-alma
   chmod +x sa-installer && ./sa-installer
   ```

### Build Process Details

The build system creates two types of binaries:

- **`sa-installer`** (`--onefile`): Single binary for distribution (~11MB)
- **`sa-shell-fast`** (`--onedir`): Directory structure for fast startup (~11MB)

**Why two binaries?**
- `--onefile`: Easy distribution, but slow startup (extracts each time)
- `--onedir`: Fast startup after first run (cached files)

Our solution: Use `--onefile` for the installer, which downloads and installs the `--onedir` version for fast performance.

### Cross-Platform Build Architecture

**macOS Build (`build_and_upload.sh`)**:
- Builds natively on macOS (ARM64)
- Uses local Python environment
- Creates macOS-compatible binaries

**Alma Linux Build (`build_alma.sh`)**:
- Builds on remote x86_64 Debian server (zubatomic.com)
- Installs Python 3.9 on the remote server
- Creates x86_64 Linux binaries compatible with Alma Linux
- Handles Python 3.5 compatibility issues automatically
- Uses tar.gz for distribution (more reliable than zip on older systems)

**Technical Notes**:
- PyInstaller doesn't support cross-compilation, so we use a remote x86_64 build server
- The Alma Linux installer handles both zip and tar.gz extraction
- All `sa` module dependencies are properly included in the PyInstaller build
- The build process is fully automated and requires no manual intervention

### Manual Build Commands

If you need to build manually:

```bash
# Build installer (--onefile)
./sa_env/bin/python -m PyInstaller --onefile --name sa-installer startup.py

# Build shell (--onedir)
./sa_env/bin/python -m PyInstaller --onedir --name sa-shell-fast sa/shell/shell.py

# Create distribution package
cd dist
zip -r sa-shell-0.1.0.zip sa-shell-0.1.0/
cd ..

# Upload manually
scp dist/sa-shell-0.1.0.zip root@zubatomic.com:/var/www/html/sa.zip
scp dist/sa-installer root@zubatomic.com:/var/www/html/sa-installer
```

### Environment Requirements

The build system requires:
- Python 3.8+
- Virtual environment with minimal dependencies (`requests`, `pyinstaller`)
- SSH access to zubatomic.com

### Types

Types that the SAObjects can have in the JSON
SATypePrimitive = Union[str, int, bool, float, None, list['SATypePrimitive'], dict[str, 'SATypePrimitive']]

Types after resolving the raw JSON into a SAObject json (basically just includes custom types)
SAType = Union[SATypeCustom, SATypePrimitive]

Types that are valid context
QueryContext = Union['ObjectList', 'SAType', 'ObjectGrouping']

Types that queries can take in or output, basically represents all types that a query will be expected to gracefully deal with 
QueryType = Union[QueryContext, 'Chain']

The arguments
Arguments = list['QueryType']

AbsorbingNone
It's similar to NoneType, but "absorbs" any operators, remaining unchanged.
All operators must be able to tolerate AbsorbingNone as context and as inputs.
The default behavior should be to pass-through the AbsorbingNone, or if in a loop just skip it (e.g filter or select).

## License

MIT License 