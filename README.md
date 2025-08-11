# Yandex Disk Dolphin Menu

KDE Dolphin file manager integration for Yandex Disk cloud storage sharing with support for multiple Linux desktop environments.

## 📚 Documentation

- **[Usage Guide](doc/USAGE_GUIDE.md)** - Installation examples, troubleshooting, and file manager-specific setup
- **[Python Version Details](doc/README_Python.md)** - Python implementation features and user-facing technical details
- **[Developer Guide](doc/DEVELOPMENT.md)** - Development workflow, CI/CD, tests, directory map (GNOME specifics)
- **[Additional Documentation](doc/additional/)** - Technical details: [Desktop Context Limitations](doc/additional/DESKTOP_CONTEXT_LIMITATIONS.md), [Migration Summary](doc/additional/MIGRATION_SUMMARY.md), [Session Improvements](doc/additional/SESSION_IMPROVEMENTS.md), [Coverage Summary](doc/additional/COVERAGE_SUMMARY.md)

> **📌 Recommendation:** The Python version is the recommended implementation with enhanced error handling and modern architecture.
### Yandex Disk integration for KDE Dolphin sub menu: use yandex cloud directory for sharing clipboard content and files between PC, mobile, people, etc..

Inspired by [yandex disk indicator](https://github.com/slytomcat/yandex-disk-indicator/wiki/Yandex-disk-indicator) context menu options

## 🖥️ File Manager Support Matrix

**Consider GNOME/GTK Beta status, so it may not work as intended**

| File Manager | Desktop | Scripts/Actions | Python Extensions | Menu Location |
|-------------|---------|-----------------|-------------------|---------------|
| **Dolphin** | KDE | ✅ Service Menus | ❌ N/A | Right-click context menu |
| **Nautilus (Files) (Beta)** | GNOME | ✅ Scripts | ✅ Optional | Scripts → "YaDisk" / Right-click |
| **Nemo (Beta)** | Cinnamon | ✅ Actions | ✅ Optional | Right-click context menu |
| **Caja (Beta)** | MATE | ✅ Actions | ✅ Optional | Right-click context menu |
| **Thunar (Beta)** | XFCE | ✅ Custom Actions | ❌ N/A | Right-click context menu |

> **Installation:** See [Usage Guide](doc/USAGE_GUIDE.md) for file manager-specific setup examples.

## 📸 Screenshots

### Menu v1.6.4
![Menu v1.6.4](https://raw.githubusercontent.com/Miheev/yaDiskDolphinMenu/main/doc/menu-v1.6.4-42.png)

### Overview
![Overview](https://raw.githubusercontent.com/Miheev/yaDiskDolphinMenu/main/doc/main-mix.png)

## ✨ Key Features

### Core Functionality
- **File Publishing**: Create public links (.com/.ru domains) with one-click sharing
- **Clipboard Integration**: Save and publish clipboard content (text and images)
- **File Operations**: Copy/move files to Yandex stream directory
- **Batch Processing**: Handle multiple files with intelligent error recovery
- **Auto-renaming**: Automatic conflict resolution with `_number` suffix pattern

### The original shell script implementation:
- **Publish file & copy ya.COM link** - Publish file and copy international link
- **Publish file & copy ya.RU link** - Publish file and copy local link
- **Publish clipboard & copy ya.COM/RU link** - Save clipboard content and publish
- **Remove public link** - Unpublish single file
- **Remove links for all copies** - Unpublish file and all numbered copies
- **Save clipboard to stream** - Save clipboard without publishing
- **Add file to stream** - Copy file to stream directory
- **Move file to stream** - Move file to stream directory

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

### Enhanced Reliability
- **Service Readiness**: Waits for yandex-disk daemon (up to 30s) before operations
- **Error Handling**: Continues processing remaining items if some fail
- **Native Notifications**: Desktop-aware notifications (kdialog/notify-send)
- **Comprehensive Logging**: Operation tracking with detailed error reporting
- **Rollback Support**: Undo operations when errors occur

### Multi-Platform Support
- **Desktop Environments**: 
  - KDE: primary, full support
  - GNOME, Cinnamon, MATE, XFCE: Beta, not tested
- **Session Types**: X11 and Wayland clipboard support
- **File Managers**: See [support matrix](#🖥️-file-manager-support-matrix) above

> **💡 Pro Tip**: Use a separate Yandex account for file sharing to prevent over-sync and maintain security boundaries.


## 📋 Requirements

### Essential Dependencies
- **yandex-disk** daemon (core functionality)
- **Python 3.8+** with venv support
- **Clipboard tools**: xclip (X11) or wl-clipboard (Wayland)
- **Notifications**: kdialog (KDE) or notify-send (GNOME/others)

### Recommended Setup
- **[yd-tools](https://github.com/slytomcat/yandex-disk-indicator)** - provides icons and additional utilities
- **File manager**: See [support matrix](#🖥️-file-manager-support-matrix) for compatibility

> **📖 Details**: See [Python Version README](doc/README_Python.md) for complete dependency information and [Usage Guide](doc/USAGE_GUIDE.md) for installation examples.


## 🚀 Quick Start

### Automated Installation (Recommended)
```bash
# 1. Install system dependencies (detects your distribution and desktop)
make install-system-deps

# 2. Install and configure Python version with desktop-aware integration
make install
make configure  # Automatically detects and configures your file manager
```

### Manual Installation Options
```bash
# Shell version only (lightweight)
./setup.sh

# Python version only (advanced features)
make install-system-deps && make install && make configure

# Both versions (maximum compatibility)
./setup.sh && make install && make configure-skip-env
```

> **📚 Detailed Examples**: See [Usage Guide](doc/USAGE_GUIDE.md) for file manager-specific installation, troubleshooting, and advanced configuration options.

### Prerequisites
1. **Install yandex-disk daemon**: Follow [official guide](https://yandex.com/support/disk-desktop-linux/)
2. **Install yd-tools** (recommended): Provides icons and utilities
3. **Configure your stream directory**: Set up where files will be copied/published

> **🔧 Setup Help**: Detailed setup instructions, file manager-specific examples, and troubleshooting are in the [Usage Guide](doc/USAGE_GUIDE.md).

## License

This project is licensed under the **Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License** (CC BY-NC-SA 4.0).

### What you can do:
- ✅ **Share** — copy and redistribute the material in any medium or format
- ✅ **Adapt** — remix, transform, and build upon the material
- ✅ **Use for personal, educational, and non-commercial purposes**

### Conditions:
- 🔗 **Attribution** — Provide appropriate credit and a link to the license
- 🚫 **NonCommercial** — No commercial use without written permission
- ♻️ **ShareAlike** — Derivatives must be licensed under CC BY-NC-SA 4.0

### Commercial Use:
For any commercial use of this software, including but not limited to:
- Use in commercial software or services
- Distribution as part of commercial products  
- Use in commercial environments or for commercial purposes
- Integration into commercial applications

**Written permission is required for any commercial use.**

For commercial licensing inquiries, please open an issue: `https://github.com/Miheev/yaDiskDolphinMenu/issues`.

See [LICENSE](LICENSE) for full terms and conditions.


## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Run quality checks: `make lint test`
5. Submit pull request


