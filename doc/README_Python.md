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

## 🔧 Technical Requirements

### Overview
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

### Python Runtime
- **Python 3.8+** with type hints support
- **Virtual Environment**: Isolated dependency management
- **Platform**: Linux (X11/Wayland session support)

### Python Dependencies (managed via requirements.txt)
```python
click >= 8.0.0          # CLI framework with decorators
pyclip >= 0.7.0         # Cross-platform clipboard (X11/Wayland auto-detect)
python-dotenv >= 1.0.0  # Environment variable management
```

### System Integration
- **yandex-disk daemon**: Core cloud storage functionality
- **Notifications**: Desktop-aware (kdialog/notify-send)
- **File Managers**: See [file manager support matrix](../README.md#🖥️-file-manager-support-matrix)

> **📦 Installation**: See [Usage Guide](USAGE_GUIDE.md) for complete installation examples and file manager-specific setup.

## 🏗️ Architecture Overview

### Core Components

**Main Script (`ydmenu.py`)**
- CLI entry point with Click decorators
- Command routing and parameter validation
- Error handling and logging coordination

**YandexDiskMenu Class**
- Core business logic and file operations
- yandex-disk daemon interaction
- Clipboard and notification management

**Environment Wrapper (`ydmenu-py-env`)**
- Virtual environment activation
- Production deployment wrapper
- PATH resolution and error handling

**Setup Script (`setup.py`)**
- Installation and configuration management
- Desktop file generation from templates
- Environment variable setup

### Data Flow

```
File Manager → ydmenu-py-env → venv/bin/python ydmenu.py → YandexDiskMenu Class
                                                          ↓
                                                   yandex-disk daemon
                                                          ↓
                                                   Yandex Cloud Storage
```

### Configuration Management

**Environment Variables (via .env)**
```bash
YA_DISK_ROOT="~/Public"              # Parent directory for Yandex Disk
YADISK_MENU_VERSION="1.6.4"          # Version tracking
```

**Runtime Configuration**
- Auto-discovery of yandex-disk paths
- Desktop environment detection
- Session type detection (X11/Wayland)

## 🔍 Development Features

### Testing Infrastructure
- **112 comprehensive unit tests** (98.2% coverage)
- **Mock-based testing**: External dependencies isolated
- **Integration testing**: End-to-end workflow validation
- **Error condition testing**: Exception handling verification

### Code Quality
- **Type hints**: Full typing support for IDE assistance
- **Linting**: flake8 and pylint integration
- **Formatting**: Black code formatter
- **Documentation**: Comprehensive docstrings

### Development Commands
```bash
make test           # Run test suite
make lint           # Code quality checks
make format         # Auto-format code
make coverage       # Coverage report
make coverage-html  # HTML coverage report
```

## 🚀 Advanced Usage

### Command Line Interface
```bash
# Direct Python usage (development)
./ydmenu.py --help
./ydmenu.py --verbose PublishToYandexCom file.txt

# Production usage (via wrapper)
ydmenu-py-env PublishToYandex file.txt
ydmenu-py-env ClipboardToStream
```

### Batch Processing Examples
```bash
# Multiple file publishing
ydmenu-py-env PublishToYandexCom file1.txt file2.txt file3.txt

# Directory operations  
ydmenu-py-env FileAddToStream /path/to/directory

# Mixed operations with error recovery
ydmenu-py-env FileMoveToStream file1.txt missing_file.txt file3.txt
# → Continues with file3.txt even if missing_file.txt fails
```

### Verbose Mode and Logging
```bash
# Enable verbose output
ydmenu-py-env --verbose PublishToYandex file.txt

# Check logs
tail -f $YA_DISK_ROOT/yaMedia-python.log
```

## 🔄 Migration from Shell Version

### Key Differences

| Feature | Shell Version | Python Version |
|---------|---------------|----------------|
| **Error Handling** | Basic | Comprehensive with recovery |
| **Batch Processing** | Limited | Full support with strategies |
| **Logging** | Simple | Detailed with levels |
| **Configuration** | Environment vars | .env + environment vars |
| **Testing** | None | 112 unit tests |
| **Type Safety** | None | Full type hints |

### Migration Path
1. **Install Python version**: `make install && make configure-skip-env`
2. **Test functionality**: Verify both versions work
3. **Gradual transition**: Use Python for new workflows
4. **Remove shell version**: When satisfied with Python version

### Compatibility
- **Shared configuration**: Both versions use same environment variables
- **Shared logging directory**: Different log files, same location
- **Shared menu structure**: Similar user experience

## 🧪 Testing and Quality Assurance

### Test Coverage
- **Main functionality**: 82 test cases covering core operations
- **Setup functionality**: 16 test cases for installation/configuration
- **Error conditions**: Comprehensive exception handling tests
- **Integration scenarios**: End-to-end workflow validation

### Continuous Integration
```bash
# Full quality check
make test && make lint && make format

# Coverage analysis
make coverage-browse  # Opens HTML report in browser
```

### Mock Strategy
- **External services**: yandex-disk daemon calls mocked
- **File operations**: Temporary directories for safe testing
- **System integration**: Desktop notifications and clipboard mocked
- **Network independence**: No external network calls in tests

### Automated Releases

- Workflow: `.github/workflows/release.yml`
- Manual trigger: GitHub → Actions → Release → Run workflow → provide `version` (e.g., `1.5.3`, `2.0.0-RC1`)
- What happens:
  - Runs `update_version.sh <version>` to update `.env`, regenerate desktop files, commit, tag `v<version>`, and push
  - Creates a GitHub Release with autogenerated notes
- Tag push trigger: Pushing a tag like `v1.5.3` also creates a Release with notes based on commits since the previous tag



## 🔗 Related Documentation

- **[Main README](../README.md)** - Project overview and file manager support matrix
- **[Usage Guide](USAGE_GUIDE.md)** - Installation examples and troubleshooting
- **[Additional Documentation](additional/)** - Technical implementation details:
  - [Desktop Context Limitations](additional/DESKTOP_CONTEXT_LIMITATIONS.md)
  - [Session Improvements](additional/SESSION_IMPROVEMENTS.md) 
  - [Migration Summary](additional/MIGRATION_SUMMARY.md)
  - [Coverage Summary](additional/COVERAGE_SUMMARY.md)

---

> **💡 Contributing**: When modifying Python code, always run `make test` to ensure compatibility and maintain test coverage. See development workflow guidelines in project documentation.
