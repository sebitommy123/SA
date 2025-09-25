# SA Framework

A Python framework for working with semantic objects and query languages.

## 🚀 Quick Start (For Users)

### Install SA from GitHub

The easiest way to get started is to install SA directly from GitHub using pip:

```bash
# Install SA from GitHub
pip install git+https://github.com/sebitommy123/SA.git
```

This will:
- Install SA and all dependencies
- Make `sa-shell` and `sa-query` commands available system-wide
- Enable `python -m sa` module execution
- Work in any Python environment

### Use SA

**Console Scripts:**
```bash
# Start interactive shell
sa-shell

# Run a single query
sa-query ".count()"

# Run with verbose output
sa-shell -v ".filter(.equals(.get_field('name'), 'John'))"

# Show help
sa-shell --help
```

**Python Module:**
```bash
# Start interactive shell
python -m sa

# Run a single query
python -m sa ".count()"

# Show help
python -m sa --help
```

**Update to Latest Version:**
```bash
# Update SA to the latest version from GitHub
sa-shell --update
# or
sa-query --update
# or
python -m sa --update
```

**Performance**: Installation takes ~10 seconds, subsequent runs are **instant**!

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
# Option 1: Use the console script (after pip install)
sa-shell

# Option 2: Use the alternative console script
sa-query

# Option 3: Run as Python module
python -m sa

# Option 4: Import and run programmatically
from sa import shell_main
shell_main()
```

## Project Structure

```
sa/
├── sa/                     # Main package
│   ├── __init__.py        # Main package entry point
│   ├── __main__.py        # Python module entry point (python -m sa)
│   ├── core/              # Core functionality
│   │   ├── __init__.py
│   │   ├── sa_object.py   # Base SAObject class
│   │   ├── object_list.py # ObjectList implementation
│   │   └── object_grouping.py # ObjectGrouping implementation
│   ├── query_language/    # Query language functionality
│   │   ├── __init__.py
│   │   ├── execute.py     # Query execution engine
│   │   ├── operators.py   # Query operators
│   │   ├── parser.py      # Query parser
│   │   └── render.py      # Result rendering
│   └── shell/             # Interactive shell
│       ├── __init__.py
│       ├── shell.py       # Shell implementation
│       └── provider_manager.py # Provider management
├── providers.txt          # Provider endpoints configuration
├── setup.py               # Package configuration with console scripts
├── pyproject.toml         # Modern Python packaging with entry points
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
sa-shell --print-profiling-information "person.count()"

# Run with debug output for detailed investigation
sa-shell --debug "lol[.best_friend.salary == 85000].count()"
```

#### Interactive Shell Profiling
```bash
# Start interactive shell
sa-shell

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
sa-shell --print-profiling-information "person.count()"
sa-shell --print-profiling-information "lol.count()"
sa-shell --print-profiling-information "#obj_A"
```

#### 2. Analyze Complex Queries
```bash
# Test complex filtering
sa-shell --print-profiling-information "lol[.best_friend.salary == 85000].count()"

# Test with debug for detailed breakdown
sa-shell --debug "lol[.best_friend.salary == 85000].count()" 2>&1 | head -20
```

#### 3. Compare Performance
```bash
# Before optimization (if applicable)
sa-shell --print-profiling-information "slow_query"

# After optimization
sa-shell --print-profiling-information "optimized_query"
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
sa-shell --debug "person.count()" 2>&1 | grep -E "(fast path|using fast)"
```

#### 2. Identify Bottlenecks
Look for operations with:
- High execution counts (> 10,000)
- Long average times (> 1ms)
- High total times (> 100ms)

#### 3. Profile Individual Components
```bash
# Test just the type filter
sa-shell --print-profiling-information "person"

# Test just the complex filter
sa-shell --print-profiling-information "lol[.best_friend.salary == 85000]"
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
$ sa-shell --print-profiling-information "person.count()"
⏱️  Profiling Summary:
   Total time: 207.9μs
   filter (23.1μs)
   count (20.0μs)
100004

# 2. Test complex query
$ sa-shell --print-profiling-information "lol[.best_friend.salary == 85000].count()"
⏱️  Profiling Summary:
   Total time: 110.204s
   filter (36.731s)
   count (24.1μs)
100000

# 3. Investigate with debug
$ sa-shell --debug "lol[.best_friend.salary == 85000].count()" 2>&1 | head -10
[filter operator runner] starting filter operation
[filter operator runner] context has 100008 objects
[filter operator runner] detected type filter at start of complex chain, pre-filtering by type: lol
```

This profiling system helps identify performance bottlenecks and guides optimization efforts for better query performance.

## 📦 Distribution & Deployment

### Publishing New Versions

SA is distributed via GitHub and installed using pip. To release a new version:

1. **Update version numbers** in `setup.py` and `pyproject.toml`
2. **Commit and push changes** to GitHub
3. **Users can update** using the built-in update command:
   ```bash
   sa-shell --update
   # or
   python -m sa --update
   ```

### Installation Methods

**Primary Method (Recommended):**
```bash
pip install git+https://github.com/sebitommy123/SA.git
```

**Alternative Methods:**
```bash
# Install from local source
pip install -e .

# Install with development dependencies
pip install -e ".[dev]"
```

### Console Scripts

After installation, the following commands are available system-wide:
- `sa-shell` - Interactive shell
- `sa-query` - Alternative shell command
- `python -m sa` - Python module execution

### Update Mechanism

The `--update` flag automatically:
- Runs `pip install --upgrade git+https://github.com/sebitommy123/SA.git`
- Installs the latest version from GitHub
- Works with any installation method

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