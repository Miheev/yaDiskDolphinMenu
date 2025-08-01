# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Yandex Disk integration for KDE Dolphin** that adds a context menu for sharing files via Yandex cloud storage. The project consists of shell scripts that extend Dolphin's right-click menu with Yandex Disk publishing and file management capabilities.

## Key Files & Architecture

- **`ydmenu.sh`** - Main logic script that handles all Yandex Disk operations (publish, unpublish, clipboard operations, file moves)
- **`ydpublish.desktop`** - KDE service menu definition that creates the Dolphin context menu entries
- **`setup.sh`** - Installation script that configures environment variables and creates symlinks
- **`open-as-root-kde5old.desktop`** - Additional desktop entry for opening folders with root privileges

## Setup & Configuration

### Bash Version Setup
1. Configure variables in `setup.sh`:
   - `YA_DISK_ROOT` - Parent directory of Yandex disk (e.g., `$HOME/Public`)
   - `YA_DISK_RELATIVE` - Yandex disk directory name (e.g., `yaDisk`)
   - `INBOX_RELATIVE` - Inbox directory for file stream (e.g., `Media`)
2. Run `./setup.sh` to set global environment variables and create symlinks
3. The script modifies `/etc/environment` and creates symlinks for `ydpublish.desktop`

### Python Version Setup (v1.0-RC-1)

#### Quick Setup (Recommended)
```bash
# Install dependencies and configure Python version
make install          # Create venv and install dependencies  
make configure        # Configure system integration (requires sudo)
```

#### Manual Setup Steps
1. Run `./setup.py` to set global environment variables and create Python-specific symlinks
2. The script creates virtual environment, installs dependencies, and symlinks `ydpublish-python.desktop`
3. Uses separate desktop file and log file to avoid conflicts with bash version
4. Desktop entries use direct execution (no `tee` logging) since Python handles its own logging

#### Alternative Setup Options
```bash
# Shell version only
./setup.sh

# Python version only  
make install && python setup.py

# Both versions (recommended for development)
./setup.sh && make install && python setup.py --skip-env
```

## Dependencies & Requirements

- KDE Linux with Dolphin file manager
- `yandex-disk` daemon installed and running
- `yd-tools` icon pack (icons in `/usr/share/yd-tools/icons/`)
- Standard Linux utilities: `kdialog`, `awk`, `xclip`, `grep`, `cut`, `iconv`
- **Python version dependencies**: `click>=8.0.0`, `pyclip>=0.7.0` (automatically managed via virtual environment)
- **Testing dependencies**: Uses Python's built-in `unittest` framework (no additional test dependencies required)

## Core Functionality

The main script (`ydmenu.sh` for bash, `ydmenu.py` for Python) handles:
- **Publishing**: Create public links for files (both .com and .ru domains)
- **Clipboard operations**: Save/publish clipboard content (text and images)
- **File management**: Copy/move files to Yandex stream directory
- **Unpublishing**: Remove public links for files and their copies
- **Error handling**: Wait for yandex-disk service readiness, show notifications
- **File naming**: Auto-rename duplicates with `_number` suffix pattern
- **Conflict resolution**: Uses rollback rename algorithm to avoid yandex-disk publish conflicts
- **Version display**: Show current version information (`ShowVersion` command)

### Python Version Enhancements (v0.5)
- **Advanced logging**: Quiet logging by default, configurable with `--verbose` flag, structured logging to separate file and console
- **Subprocess logging**: All subprocess calls (yandex-disk, xclip) always log stderr; stdout only logged in verbose mode
- **Improved clipboard**: Native cross-platform clipboard access via `pyclip` with `xclip` fallback for edge cases
- **Better error handling**: Comprehensive logging of command failures with return codes and output
- **Robust conflict resolution**: Rollback rename algorithm prevents yandex-disk publish failures
- **Separate log files**: Uses `yaMedia-python.log` to avoid conflicts with bash version logs

## Configuration Variables

Runtime configuration is done through environment variables:
- `YA_DISK_ROOT` - Parent directory of Yandex disk (e.g., `$HOME/Public`)
- Derived paths:
  - `yaDisk` - `$YA_DISK_ROOT/yaMedia` (Yandex disk root directory)
  - `streamDir` - `$YA_DISK_ROOT/yaMedia/Media` (inbox/stream directory for file operations)
  - `logFilePath` - `$YA_DISK_ROOT/yaMedia.log` (bash version log file)
  - `logFilePath` - `$YA_DISK_ROOT/yaMedia-python.log` (Python version log file)

### Python Version Logging
- **File logging**: Always INFO level to `$YA_DISK_ROOT/yaMedia-python.log`
- **Console logging**: INFO level by default (quiet mode), DEBUG level with `--verbose` flag
- **Structured format**: `timestamp - logger_name - level - message`
- **Subprocess logging**: Command execution and stderr always logged; stdout only logged in verbose mode
- **Separate log files**: Python version uses `yaMedia-python.log` to avoid conflicts with bash version
- **Default quiet**: Quiet logging is enabled by default for cleaner output experience

Bash operations are logged to `$YA_DISK_ROOT/yaMedia.log`.
Python operations are logged to `$YA_DISK_ROOT/yaMedia-python.log`.

## Usage Examples

### Installation and Setup

#### Quick Installation with Make
```bash
# Clone the repository
git clone <repository-url>
cd yaDiskDolphinMenu

# Install Python version (recommended)
make install          # Install dependencies in virtual environment
make configure        # Configure system integration (requires sudo)
make status          # Check installation status
```

#### Make Commands Reference
```bash
make help            # Show all available commands
make install         # Install Python dependencies  
make configure       # Configure Python version (requires sudo)
make test           # Run unit tests
make lint           # Run code linting
make format         # Format code with black
make clean          # Clean up generated files
make status         # Show installation status
make uninstall      # Remove symlinks (keeps files)
```

### Python Version (v1.0-RC-1)

#### Command Line Usage
```bash
# Basic commands (quiet logging by default)
ydmenu.py PublishToYandexCom /path/to/file.txt
ydmenu.py ClipboardPublish
ydmenu.py FileAddToStream /path/to/file.txt
ydmenu.py ShowVersion

# Verbose mode to enable detailed logging
ydmenu.py --verbose PublishToYandexCom /path/to/file.txt
ydmenu.py -v ClipboardPublish
```

#### Available Commands
- `PublishToYandexCom` - Publish file and copy .com link to clipboard
- `PublishToYandex` - Publish file and copy .ru link to clipboard  
- `ClipboardPublishToCom` - Save clipboard content and publish with .com link
- `ClipboardPublish` - Save clipboard content and publish with .ru link
- `UnpublishFromYandex` - Remove public link from file
- `UnpublishAllCopy` - Remove public links from file and all numbered copies
- `ClipboardToStream` - Save clipboard content to stream directory
- `FileAddToStream` - Copy file to stream directory
- `FileMoveToStream` - Move file to stream directory
- `ShowVersion` - Display version information

#### Logging Features
```bash
# Quiet logging by default - shows only essential info and errors
ydmenu.py PublishToYandexCom file.txt

# Use verbose mode to see detailed subprocess output
ydmenu.py --verbose PublishToYandexCom file.txt

# Check log file for detailed operation history
tail -f $YA_DISK_ROOT/yaMedia-python.log

# Log always includes:
# - Command execution details
# - Subprocess stderr (errors always visible)
# - Clipboard operations (pyclip vs xclip fallback)
# - File conflict resolution
# - Error details with return codes

# Verbose mode additionally shows:
# - Subprocess stdout (command output)
# - Debug-level information
```

#### Clipboard Integration
The Python version provides improved clipboard handling:
- **Primary**: Uses `pyclip` for cross-platform text and binary clipboard access
- **Fallback**: Uses `xclip` when pyclip is unavailable or fails
- **Auto-detection**: Automatically detects clipboard content type (text vs image)
- **Smart naming**: Creates meaningful filenames based on clipboard text content

#### Development and Testing

Using Make (Recommended):
```bash
# Setup development environment
make install         # Create venv and install dependencies
make test           # Run unit tests  
make test-coverage  # Run tests with coverage report
make lint           # Run code linting (flake8, pylint)
make format         # Format code with black
make clean          # Clean up generated files
make status         # Check installation status
```

Manual Development Setup:
```bash
# Use the same virtual environment created by setup.py for both production and testing
./setup.py               # Creates venv and installs dependencies

# Run unit tests using the production venv
source venv/bin/activate
python test_ydmenu.py

# Or run tests with pytest if available
python -m pytest test_ydmenu.py -v

# The venv contains all production dependencies (click, pyclip) needed for both runtime and testing
```

#### Rollback Rename Algorithm

The Python version implements a sophisticated conflict resolution algorithm to prevent `yandex-disk publish` failures:

**Problem**: When publishing files outside the Yandex disk directory, conflicts occur if a file with the same name already exists in the Yandex disk directory. This causes `yandex-disk publish` to fail with "path already exists" error.

**Solution**: Rollback rename algorithm
1. **Detect conflict**: Check if destination name conflicts with existing files
2. **Temporary rename**: Rename source file with timestamp suffix (e.g., `file_temp_1672531234.txt`)
3. **Execute operation**: Run yandex-disk publish/copy/move on temporarily renamed file
4. **Automatic rename**: Yandex-disk automatically uses the unique destination name
5. **Rollback**: For copy operations, rename source file back to original name

**Example**:
```bash
# Scenario: Publishing /home/user/file.txt when yaMedia/file.txt already exists
# 1. Temporarily rename: /home/user/file.txt -> /home/user/file_temp_1672531234.txt
# 2. Publish temporary file (succeeds)
# 3. Move to stream: yaMedia/Media/file_1.txt (auto-generated unique name)
# 4. For outside files: source gets moved, no rollback needed
# 5. For inside files: rename back to original name
```

**Benefits**:
- Eliminates "path already exists" errors
- Preserves source files for copy operations
- Automatic conflict resolution with numbered suffixes
- Robust error handling with guaranteed rollback

### Troubleshooting

#### Installation Issues
```bash
# Check current installation status
make status

# Clean and reinstall if needed
make clean
make install
make configure

# Check system dependencies
make check-deps

# Check if yandex-disk is running
yandex-disk status
```

#### Common Issues and Solutions
```bash
# Permission denied during configure
sudo make configure

# Missing dependencies
make install

# Tests failing
make clean && make test

# Remove installation completely
make uninstall
make clean
```

#### Monitoring and Debugging  
```bash
# Monitor operations in real-time
tail -f $YA_DISK_ROOT/yaMedia-python.log

# Run with verbose logging
ydmenu.py --verbose <command> <args>

# Check system status
make status
```