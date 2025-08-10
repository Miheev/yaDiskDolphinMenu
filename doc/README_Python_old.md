# Yandex Disk Menu - Python Version

A modern Python implementation of the Yandex Disk file manager integration with enhanced error handling, batch processing, and multi-platform support.

> **📚 Documentation**: For installation examples and troubleshooting, see [Usage Guide](USAGE_GUIDE.md). For project overview, see [Main README](../README.md).

## 🐍 Python-Specific Features

### Advanced Processing
- **Batch Operations**: Intelligent batch processing with two strategies:
  - **One-by-One**: Publish/save operations with progress notifications and link collection
  - **All-at-Once**: Optimized file copy/move operations for maximum efficiency
- **Error Recovery**: Continue processing remaining items when some fail
- **Rollback Support**: Automatic rollback of operations when errors occur
- **Conflict Resolution**: Smart auto-renaming with `_number` suffix pattern

### Modern Architecture
- **Type Safety**: Full type hints for better IDE support and reliability
- **Modular Design**: Clean separation of concerns with dedicated classes
- **Configuration Management**: `.env` file-based configuration with dotenv
- **CLI Framework**: Built on Click for robust command-line interface
- **Cross-Platform**: Automatic X11/Wayland clipboard detection via pyclip

### Enhanced Reliability
- **Comprehensive Logging**: Detailed operation tracking with verbose mode
- **Service Readiness**: Waits for yandex-disk daemon before operations
- **Input Validation**: Robust file path and parameter validation
- **Graceful Degradation**: Fallback mechanisms for missing dependencies

## Requirements

### System Dependencies
- **Desktop Environment**: 
  - **KDE** with Dolphin file manager (primary support)
  - **GNOME/GTK** with Files/Nautilus, Nemo, Caja, or Thunar [Beta]
- **yandex-disk** daemon installed and running
- **Notifications**: **kdialog** (KDE) or **notify-send** (GNOME and others)
- **Clipboard utilities**:
  - **xclip** - For X11 environments
  - **wl-clipboard** - For Wayland environments
- **Python 3.8+**
- **Python venv** - python3-venv package (naming varies by distribution)

### Python Dependencies
- click >= 8.0.0
- pyclip >= 0.7.0 (automatically switches between xclip/wl-clipboard)
- python-dotenv >= 1.0.0

## Installation

### Automated System Dependencies

Install system dependencies automatically based on your Linux distribution:
```bash
make install-system-deps  # Detects package manager and session type (X11/Wayland)
```

This will install appropriate packages for your distribution (APT/DNF/Pacman) and session type.

### Installation Options

You can install either version independently or both together:

### Shell Version Only (Original)
```bash
# Use the original shell setup script
./setup.sh
```

### Python Version Only
```bash
# Install Python version with virtual environment and desktop-aware integration
make install-system-deps        # install virtual environment support, clipboard tools, etc.
make install               # Sets up venv and dependencies
make configure             # Configure Python version with desktop-aware file manager integration (requires sudo)
# Alternatively run
# python setup.py

# Or manually:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python setup.py --check-deps  # Check dependencies
python setup.py               # Full setup
```

### Both Versions (Recommended)
```bash
# Install shell version first
./setup.sh

# Then install Python version
make install-system-deps
make install
make configure-skip-env  # Skip env vars (already set by setup.sh)
# Alternatively run
# python setup.py --skip-env
```

### Custom Python Configuration
```bash
# Custom paths for Python version
python setup.py --ya-disk-root ~/MyCloud --ya-disk-relative MyDisk --inbox-relative Inbox

# Python setup without environment variable changes
python setup.py --skip-env
```

## Usage

After installation, right-click any file in Dolphin to access **both** versions:

### YaDisk (Shell Version)
The original shell script implementation:
- **Publish file & copy ya.COM link** - Publish file and copy international link
- **Publish file & copy ya.RU link** - Publish file and copy local link  
- **Publish clipboard & copy ya.COM/RU link** - Save clipboard content and publish
- **Remove public link** - Unpublish single file
- **Remove links for all copies** - Unpublish file and all numbered copies
- **Save clipboard to stream** - Save clipboard without publishing
- **Add file to stream** - Copy file to stream directory
- **Move file to stream** - Move file to stream directory

### YaDisk (Python)
The new Python implementation with the same functionality but improved error handling and logging.

## Development

### Setup Development Environment
```bash
make setup-dev
```

### Run Tests
```bash
make test                # Run unit tests
make test-coverage      # Run tests with coverage report
```

### Code Quality
```bash
make lint               # Run linting
make format             # Format code with black
```

### Other Commands
```bash
make status            # Show installation status
make clean             # Clean up generated files
make uninstall         # Remove symlinks
make help              # Show all available commands
```

## Configuration

### Environment Variables
- `YA_DISK_ROOT` - Parent directory of Yandex disk (set by setup script)

### Directory Structure
```
$YA_DISK_ROOT/
├── yaMedia/           # Main Yandex disk directory
│   └── Media/         # Stream directory for file operations
└── yaMedia.log        # Operation log file
```

### Icon Configuration
Icons are expected at `/usr/share/yd-tools/icons/`:
- `yd-128.png` - Main icon
- `yd-128_g.png` - Warning icon  
- `light/yd-ind-error.png` - Error icon

## Architecture

### Core Components

**Shell Version:**
- **`ydmenu.sh`** - Original shell script implementation
- **`setup.sh`** - Shell setup script (handles shell files only)
- **`ydpublish.desktop`** - KDE service menu for shell version

**Python Version:**  
- **`ydmenu.py`** - Python rewrite with improved features
- **`setup.py`** - Python setup script (handles Python files only)
- **`ydpublish-python.desktop`** - KDE service menu for Python version
- **`ydmenu-py-env`** - Wrapper script for virtual environment activation
- **`test_*.py`** - Comprehensive unit tests for Python code

### Key Improvements Over Shell Version
- **Multiple Item Processing** - Process multiple files/directories with intelligent algorithms optimized for different operation types
- **Enhanced Parameter Logging** - Comprehensive logging of input parameters, file details, and processing steps
- **Better Error Handling** - Comprehensive exception handling with proper logging, continues processing remaining items on failures
- **Optimized Architecture** - Centralized constants, clean separation of concerns, and improved code organization
- **Type Safety** - Python type hints for better code reliability
- **Modular Design** - Object-oriented structure for better maintainability
- **Testing** - Full unit test coverage with mocking (52+ test cases)
- **Configuration** - Flexible command-line configuration options
- **Documentation** - Comprehensive inline documentation

### Class Structure
```python
class YandexDiskMenu:
    ├── __init__()                    # Initialize configuration
    ├── log_message()                 # Logging functionality
    ├── show_notification()           # KDE notifications
    ├── wait_for_ready()              # Service readiness check
    ├── get_clipboard_content()       # Clipboard operations
    ├── publish_file()                # File publishing
    ├── unpublish_file()              # Single file unpublishing
    ├── unpublish_copies()            # Batch unpublishing
    ├── sync_yandex_disk()            # Sync operations
    └── generate_unique_filename()    # Conflict resolution
```

## Troubleshooting

### Check Installation Status
```bash
make status
```

### Common Issues

1. **Service not available**
   ```bash
   yandex-disk status
   yandex-disk start
   ```

2. **Missing dependencies**
   ```bash
   # Install yandex-disk
   # Install kdialog (usually part of KDE)
   sudo apt install xclip  # or equivalent for your distro
   ```

3. **Desktop menu not appearing**
   - Restart Dolphin
   - Check symlinks: `make status`
   - Verify KDE service menu directories exist

4. **Permission errors**
   - Ensure scripts are executable: `chmod +x ydmenu.py setup.py`
   - Check virtual environment permissions

### Logging
All operations are logged to `$YA_DISK_ROOT/yaMedia.log` with timestamps and detailed error information.

## Choosing Between Shell and Python Versions

Both versions are installed and available simultaneously:

### Shell Version (ydmenu.sh)
- **Lightweight** - No additional dependencies beyond system tools
- **Fast startup** - Direct shell execution
- **Proven** - Original tested implementation
- **Compatible** - Works on minimal systems

### Python Version (ydmenu.py)
- **Better error handling** - Comprehensive exception handling with logging
- **Type safety** - Python type hints for reliability  
- **Extensible** - Easier to modify and extend
- **Testing** - Full unit test coverage
- **Modern** - Uses modern Python practices

### Setup Script Separation
Each version has its own setup script with focused responsibilities:

**`setup.sh` (Shell version):**
- Configures environment variables in `/etc/environment`
- Makes `ydmenu.sh` executable
- Creates symlinks for `ydpublish.desktop` 
- Handles shell script PATH setup

**`setup.py` (Python version):**
- Creates and manages Python virtual environment
- Installs Python dependencies
- Makes `ydmenu.py` and `ydmenu-py-env` executable
- Creates symlinks for `ydpublish-python.desktop`
- Sets up `ydmenu-py-env` wrapper in `~/bin`

### Using Both Versions
You can use either version as they both:
- Use the same configuration and environment variables
- Work with the same directory structure  
- Support all the same operations
- Log to the same file (`$YA_DISK_ROOT/yaMedia.log`)

The Python version automatically uses its virtual environment when called via the `ydmenu-py-env` wrapper script from the desktop menu.

## Technical Details

### Clipboard Compatibility

The Python version uses **pyclip** for clipboard operations, which automatically switches between:
- **xclip** on X11 environments
- **wl-clipboard** on Wayland environments

This provides seamless cross-platform clipboard support without manual configuration. The bash version also supports both environments with automatic detection.

### Environment Detection

Both versions automatically detect:
- **Display Server**: X11 vs Wayland (via `WAYLAND_DISPLAY` and `XDG_SESSION_TYPE`)
- **Clipboard Tools**: Uses appropriate clipboard utility for the detected environment
- **Notification System**: Prefers `kdialog` (KDE)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Run quality checks: `make lint test`
5. Submit pull request

## License

This project is licensed under the **Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License** (CC BY-NC-SA 4.0). Derivative works must be distributed under the same license. Commercial use requires prior written permission from the copyright holder.

See the root [LICENSE](../LICENSE) for full terms.

### Additional Documentation
- See `doc/additional/` for deeper context:
  - Desktop Context Limitations
  - Migration Summary (frozen)
  - Session Improvements
  - Coverage Summary