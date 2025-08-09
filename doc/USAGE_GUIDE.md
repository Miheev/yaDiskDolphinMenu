# Yandex Disk Dolphin Menu - Usage Guide

## System Requirements

### Clipboard Support

Both versions support **X11** and **Wayland** environments automatically:
- **X11**: Uses `xclip` for clipboard operations
- **Wayland**: Uses `wl-clipboard` for clipboard operations

The Python version uses `pyclip` which automatically detects and switches between these tools based on your session type.

### Automated Dependency Installation

Install system dependencies for your distribution:
```bash
make install-system-deps  # Detects package manager (APT/DNF/Pacman) and session type
```

## Quick Start

### Choose Your Installation Approach

You can install either version independently or both together. Here's what each approach gives you:

| Approach | Benefits | When to Use |
|----------|----------|-------------|
| **Shell Only** | Lightweight, fast, minimal dependencies | Production systems, minimal setups |
| **Python Only** | Better error handling, modern code, extensible | Development, testing, feature-rich usage |
| **Both Versions** | Maximum flexibility, can compare both | Development, migration period, user choice |

### Installation Commands

#### Shell Version Only (Lightweight)
```bash
./setup.sh
```
- Sets environment variables in `/etc/environment`
- Creates desktop menu: **"YaDisk"**
- Uses `ydmenu.sh` directly

#### Python Version Only (Modern)
```bash
make install-system-deps        # install virtual environment support for python, etc..
make install               # Install dependencies and check system
make configure             # Configure Python version (requires sudo for env vars)
```
- Creates virtual environment with dependencies
- Creates desktop menu: **"YaDisk (Python)"**
- Uses `ydmenu-py-env` wrapper for venv activation

#### GNOME Integration (Files 48+)
```bash
make gnome-install   # Install Nautilus Scripts and optional Nemo/Caja actions
make gnome-status    # Check scripts/actions presence and permissions
make gnome-uninstall # Remove GNOME scripts/actions
```
- Files (Nautilus): Actions appear under the **Scripts** submenu as "YaDisk – ..."
- Nemo/Caja: Actions appear in the context menu if the file manager is installed
- Restart the file manager after installation: `nautilus -q`, `nemo -q`, or `caja -q`

#### Both Versions (Recommended)
```bash
# Install shell version first (sets environment variables)
./setup.sh

# Then install Python version (skips env setup)
make install-system-deps
make install
make configure-skip-env # Skip environment variables (already set)
# Alternatively run
# python setup.py --skip-env
```
- Gets both desktop menus: **"YaDisk"** and **"YaDisk (Python)"**
- Shared configuration and log files
- Can use either version as needed

## Using the Context Menus

After installation, right-click any file in Dolphin to see available options. In GNOME Files, use the **Scripts** submenu.

### Shell Version Menu: "YaDisk"
- Direct shell script execution
- Fast startup (~0.1s)
- Minimal memory usage (~2MB)

### Python Version Menu: "YaDisk (Python)"
- Automatic virtual environment activation
- Enhanced error handling and logging
- Slightly slower startup (~0.3s, includes venv activation)

### Available Actions (Both Versions)
- **Publish file & copy ya.COM link** - International sharing
- **Publish file & copy ya.RU link** - Local sharing
- **Publish clipboard & copy link** - Share clipboard content
- **Remove public link** - Unpublish single file
- **Remove links for all copies** - Unpublish file and numbered copies
- **Save clipboard to stream** - Save without publishing
- **Add/Move file to stream** - File management operations

## Development Workflow

### Setting Up Development Environment
```bash
# Install both versions for testing
./setup.sh && make install-system-deps && make install && make configure-skip-env

# Set up Python development environment
make setup-dev

# Check installation status
make status
```

### Testing
```bash
# Run Python unit tests
make test

# Run tests with coverage
make test-coverage

# Check code quality
make lint
make format
```

### Debugging Issues
```bash
# Check system status
make status

# View detailed logs
tail -f $YA_DISK_ROOT/yaMedia.log

# Check yandex-disk service
yandex-disk status
```

## Configuration Management

### Environment Variables (Set by either setup script)
- `YA_DISK_ROOT` - Parent directory of Yandex disk
- `PATH` - Updated to include `~/bin` for script access

### Directory Structure
```
$YA_DISK_ROOT/
├── yaMedia/           # Main Yandex disk directory
│   └── Media/         # Stream directory for operations
└── yaMedia.log        # Shared log file for both versions
```

### Custom Configuration
```bash
# Python version with custom paths
python setup.py --ya-disk-root ~/MyCloud --ya-disk-relative MyDisk

# Shell version (edit setup.sh variables before running)
# Edit YA_DISK_ROOT and YA_DISK_RELATIVE in setup.sh
./setup.sh
```

## Maintenance & Management

### Checking Installation Status
```bash
make status
```
Shows:
- Virtual environment status
- Dependencies installation
- Script permissions
- System dependencies (yandex-disk, kdialog, xclip)
- Symlink status for both versions
- Desktop file installation

### Updating
```bash
# Update Python dependencies
make install-system-deps
make install

# Update Python setup
python setup.py --check-deps

# Reinstall symlinks if needed
python setup.py --skip-env  # Python version
./setup.sh                  # Shell version
```

### Uninstalling
```bash
# Remove symlinks (keeps original files)
make uninstall

# Clean Python build files
make clean

# Manual cleanup
rm -rf venv/
rm -f ~/bin/ydmenu*
rm -f ~/.local/share/kservices5/ServiceMenus/ydpublish*.desktop
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Desktop Menu Not Appearing
```bash
# Check symlinks
make status

# Restart Dolphin
killall dolphin && dolphin &

# Verify KDE directories exist
mkdir -p ~/.local/share/kservices5/ServiceMenus/
mkdir -p ~/.local/share/kio/servicemenus/
```

#### 2. Python Version Not Working
```bash
# Check virtual environment
ls venv/bin/python

# Test wrapper script
ydmenu-py-env --help

# Check dependencies
make install-system-deps
make install
```

#### 3. Permission Errors
```bash
# Make scripts executable
chmod +x ydmenu.py setup.py ydmenu-py-env ydmenu.sh setup.sh

# Check file ownership
ls -la ydmenu*
```

#### 4. Yandex Disk Service Issues
```bash
# Check service status
yandex-disk status

# Start service if needed
yandex-disk start

# Check daemon configuration
yandex-disk status --tray
```

#### 5. Environment Variables Not Set
```bash
# Check environment
echo $YA_DISK_ROOT

# Reload environment (after setup)
source /etc/environment

# Log out and back in for system-wide effect
```

### Debugging Tips

1. **Check logs**: All operations log to `$YA_DISK_ROOT/yaMedia.log`
2. **Test manually**: Run scripts directly to see detailed error messages
3. **Verify paths**: Ensure all paths in environment variables exist
4. **Check dependencies**: Use `make status` to verify all system dependencies

## Performance Comparison

| Aspect | Shell Version | Python Version |
|--------|--------------|----------------|
| Startup Time | ~0.1s | ~0.3s (includes venv) |
| Memory Usage | ~2MB | ~15MB |
| Dependencies | System tools only | Python + click + PyQt5 |
| Error Handling | Basic | Comprehensive |
| Extensibility | Limited | High |
| Testing | Manual | Unit tests |

## Migration Strategy

### From Shell to Python
1. Install Python version alongside shell: `make install-system-deps && make install && make configure-skip-env`
2. Test Python version functionality
3. Gradually switch to using Python menus
4. Keep shell version as backup until confident

### Development Workflow
1. Develop/test with Python version (better debugging)
2. Verify compatibility with shell version
3. Deploy based on environment requirements

### Production Deployment
- **Minimal environments**: Shell version only
- **Development/feature-rich**: Python version only  
- **Migration period**: Both versions available

## Support and Maintenance

### File Structure Overview
```
yaDiskDolphinMenu/
├── # Shell Version Files
│   ├── ydmenu.sh              # Main shell script
│   ├── setup.sh               # Shell setup script
│   └── ydpublish.desktop      # Shell desktop file
├── # Python Version Files  
│   ├── ydmenu.py              # Main Python script
│   ├── setup.py               # Python setup script
│   ├── ydpublish-python.desktop # Python desktop file
│   ├── ydmenu-py-env          # Python wrapper script
│   ├── requirements.txt       # Python dependencies
│   ├── venv/                  # Virtual environment
│   ├── test_*.py              # Unit tests
│   └── Makefile               # Development automation
└── # Shared Documentation
    ├── README_Python.md       # Main documentation
    ├── MIGRATION_SUMMARY.md   # Migration details
    ├── USAGE_GUIDE.md         # This file
    └── CLAUDE.md              # Project context
```

### Key Design Principles

1. **Separation of Concerns**: Each setup script handles only its own files
2. **Non-Destructive**: Both versions coexist without conflicts
3. **Shared Configuration**: Common environment variables and log files
4. **Independent Operation**: Either version works alone or together
5. **Backward Compatibility**: Original shell functionality preserved

This dual approach provides maximum flexibility while maintaining reliability and allowing gradual migration or permanent coexistence based on user needs.