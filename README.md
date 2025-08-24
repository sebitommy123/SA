# SA Framework

A Python framework for working with semantic objects and query languages.

## 🚀 Quick Start (For Users)

### Install the SA Shell

The easiest way to get started is with our pre-built shell:

```bash
# Download and run the installer
curl -L -o sa-installer https://zubatomic.com/sa-installer
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

# Create a list of objects
objects = ObjectList([obj])
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
├── flask_providers/
│   ├── providers.txt      # Provider endpoints configuration
│   └── resources/
│       └── simple_objects.json
├── scripts/               # Utility scripts
│   ├── build_and_upload.sh
│   ├── build_binary.sh
│   └── startup.py
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

## 📦 Distribution & Deployment

### Building and Uploading New Versions

To release a new version of the SA Shell:

1. **Ensure you have access to zubatomic.com** (SSH key configured)

2. **Run the build and upload script**:
   ```bash
   ./scripts/build_and_upload.sh
   ```

   This script will:
   - Build the installer binary (`sa-installer`) using PyInstaller `--onefile`
   - Build the shell binary (`sa-shell-fast`) using PyInstaller `--onedir`
   - Create a distribution package (`sa-shell-0.1.0.zip`)
   - Upload both files to zubatomic.com via SCP

3. **Files uploaded**:
   - `zubatomic.com/sa.zip` ← Distribution package
   - `zubatomic.com/sa-installer` ← Installer binary

4. **Users can then install**:
   ```bash
   curl -L -o sa-installer https://zubatomic.com/sa-installer
   chmod +x sa-installer
   ./sa-installer
   ```

### Build Process Details

The build system creates two types of binaries:

- **`sa-installer`** (`--onefile`): Single binary for distribution (~11MB)
- **`sa-shell-fast`** (`--onedir`): Directory structure for fast startup (~11MB)

**Why two binaries?**
- `--onefile`: Easy distribution, but slow startup (extracts each time)
- `--onedir`: Fast startup after first run (cached files)

Our solution: Use `--onefile` for the installer, which downloads and installs the `--onedir` version for fast performance.

### Manual Build Commands

If you need to build manually:

```bash
# Build installer (--onefile)
./sa_env/bin/python -m PyInstaller --onefile --name sa-installer ./scripts/startup.py

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

## License

MIT License 