# Yandex Disk Menu - Usage Guide & Examples

This guide provides detailed installation examples, file manager-specific setup, and troubleshooting instructions.

> **📋 Overview**: For project introduction and quick start, see [README](../README.md). For Python technical details, see [Python README](README_Python.md).

## 🚀 Quick Command Reference

| Desktop Environment | Recommended Setup Command |
|---------------------|---------------------------|
| **Any Desktop (Auto-detect)** | `make install-system-deps && make install && make configure` |
| **Existing YA_DISK_ROOT** | `make install-system-deps && make install && make configure-skip-env` |
| **Shell only (KDE)** | `./setup.sh` |

### Common Use Cases

**🎯 Most users:** Use auto-detection (`make configure`)  
**⚡ Minimal setup:** Use shell version (`./setup.sh`)  
**🔧 Granular control:** Use individual component commands (`gnome-install`, `gnome-ext-install`)  
**🚫 Existing config:** Use skip environment variables (`make configure-skip-env`)

## 🖥️ File Manager-Specific Installation

### KDE Dolphin (Primary Support)

**Setup:**
```bash
make install-system-deps  # Install KDE dependencies (notification, clipboard tools)
make install && make configure  # Auto-detects KDE and configures for Dolphin
```

**Alternative (Shell only):**
```bash
./setup.sh  # Lightweight shell version
```

**Menu Location:** Right-click on files → "YaDisk" or "YaDisk (Python)"

---

### GNOME Nautilus (Files) [Beta]

> **💡 Integration Types**: 
> - **`make gnome-install`** - Scripts/actions integration (works everywhere, basic functionality)
> - **`make gnome-ext-install`** - Python extensions integration (enhanced functionality, requires specific packages)

**Setup:**
```bash
# Install GNOME dependencies and configure everything at once
make install-system-deps
make install && make configure  # Auto-detects GNOME and configures all file managers

# Or skip environment variable setup
make install && make configure-skip-env
```

**Manual Granular Installation:**
```bash
# 1. Basic scripts installation (works everywhere)
make gnome-install  # Installs Nautilus scripts

# 2. Enhanced Python extension (if python3-nautilus available)
make gnome-ext-install  # Requires python3-nautilus package

# 3. Restart file manager
nautilus -q
```

**Menu Locations:**
- **Scripts**: Files → Scripts → "YaDisk – ..." (always available)
- **Extension**: Right-click context menu → "YaDisk" (enhanced integration)

**Dependencies:**
- **Scripts**: `libnotify-bin` (notifications)
- **Extension**: `python3-nautilus`, `python3-gi`, `gir1.2-gtk-3.0`

---

### Nemo (Cinnamon) [Beta]

**Setup:**
```bash
make install-system-deps  # Install dependencies
make install && make configure  # Auto-detects Nemo

# Optional: Python extension
sudo apt install python3-nemo  # If available
make nemo-ext-install
nemo -q  # Restart Nemo
```

**Manual Commands:**
```bash
# Actions only
make gnome-install  # Installs .nemo_action files

# Check status
make nemo-ext-status
```

**Menu Location:** Right-click context menu → "YaDisk – ..."

---

### Caja (MATE) [Beta]

**Setup:**
```bash
make install-system-deps
make install && make configure  # Auto-detects Caja

# Optional: Python extension  
sudo apt install python3-caja  # If available
make caja-ext-install
caja -q  # Restart Caja
```

**Manual Commands:**
```bash
# Actions only
make gnome-install  # Installs .desktop action files

# Check status
make caja-ext-status
```

**Menu Location:** Right-click context menu → "YaDisk – ..."

---

### Thunar (XFCE) [Beta]

**Setup:**
```bash
make install-system-deps
make install && make configure  # Auto-detects Thunar

# Manual installation
make thunar-install  # Merges custom actions into uca.xml
```

**Manual Commands:**
```bash
# Check installation
make thunar-status

# Remove (if needed)
make thunar-uninstall
```

**Menu Location:** Right-click context menu → "YaDisk – ..."

**Note:** Thunar uses custom actions (XML), not Python extensions.

---

## 🔧 Configuration Commands

### Main Configuration
```bash
make configure            # Auto-detect desktop and configure (recommended)
make configure-skip-env   # Auto-detect desktop, skip environment variables
```

**What `make configure` does:**
- **Detects desktop environment** (KDE, GNOME, etc.)
- **KDE**: Configures Dolphin service menus
- **GNOME**: Installs scripts/actions + Python extensions for all file managers
- **Unknown**: Universal configuration with manual file manager setup

### Component Commands (Advanced Users)
```bash
# GNOME/GTK file managers (manual control)
make gnome-install        # Install scripts/actions for all file managers
make gnome-ext-install    # Install Python extensions for all supported file managers
make gnome-status         # Check scripts/actions status
make gnome-ext-status     # Check Python extensions status
make gnome-uninstall      # Remove all scripts/actions
make gnome-ext-uninstall  # Remove all Python extensions

# Status & Maintenance
make status               # Overall installation status
make test                 # Run all tests
make clean                # Clean build files
make uninstall            # Remove Python version
```

## 🔧 Installation Options Comparison

| Method | Speed | Features | When to Use |
|--------|-------|----------|-------------|
| **Desktop-specific** (`make configure-kde/gnome`) | Fast | Targeted for your desktop | **Recommended** - Optimized setup |
| **Auto-detect** (`make configure`) | Fast | Auto-detects your environment | Good for mixed/uncertain environments |
| **Shell only** (`./setup.sh`) | Fastest | Basic features, minimal deps | Lightweight systems, KDE only |
| **Manual components** | Slower | Full control over components | Troubleshooting, custom setups |

## 📱 System Requirements

### Clipboard Support
- **X11**: Uses `xclip` for clipboard operations
- **Wayland**: Uses `wl-clipboard` for clipboard operations  
- **Python**: Uses `pyclip` (auto-detects and switches)

### Dependencies by Desktop
| Desktop | Required | Optional Extensions |
|---------|----------|-------------------|
| **KDE** | `kdialog`, `xclip`/`wl-clipboard` | None |
| **GNOME** | `libnotify-bin`, clipboard tools | `python3-nautilus`, `python3-gi` |
| **Others** | `notify-send`, clipboard tools | Desktop-specific packages |

### Automated Installation
```bash
make install-system-deps  # Detects your distribution and desktop
```

**Supported Package Managers:**
- **APT** (Ubuntu/Debian)
- **DNF** (Fedora/Red Hat)  
- **Pacman** (Arch Linux)

## 🎯 Real-World Usage Examples

### Installation Scenarios

**Scenario 1: Fresh Ubuntu Desktop (GNOME)**
```bash
# Complete automated setup
make install-system-deps  # Installs libnotify-bin, python3-nautilus
make install && make configure-gnome
# Result: Scripts + Python extensions in Nautilus
```

**Scenario 2: Linux Mint (Cinnamon/Nemo)**
```bash
# Nemo-optimized setup
make install-system-deps  # Installs nemo extensions
make install && make configure-gnome  # Auto-detects Nemo
make nemo-ext-status  # Verify extension installation
```

**Scenario 3: Corporate KDE Environment (No sudo)**
```bash
# Shell version only (no sudo required for env setup)
./setup.sh
# Result: Basic YaDisk menu in Dolphin
```

**Scenario 4: Development Machine (Multiple File Managers)**
```bash
# Install everything for testing
make install-system-deps && make install
make configure-gnome  # Sets up all detected file managers
make gnome-status     # Check what was installed
```

**Scenario 5: Existing Yandex Disk Setup**
```bash
# Don't modify existing YA_DISK_ROOT environment variable
make install && make configure-kde-skip-env
# or
make install && make configure-gnome-skip-env
```

### Component-Specific Use Cases

**Use Case: Basic Integration (All File Managers)**
```bash
make gnome-install        # Scripts/actions for Nautilus, Nemo, Caja, Thunar
# Result: Menu items available in all supported file managers
```

**Use Case: Enhanced Integration (Python Extensions)**
```bash
make gnome-ext-install    # Python extensions for all supported file managers
# Result: Advanced integration where supported (auto-detects capabilities)
```

**Use Case: Development Testing**
```bash
# Install everything for comprehensive testing
make gnome-install        # All scripts/actions
make gnome-ext-install    # All Python extensions
make gnome-status         # Check scripts status
make gnome-ext-status     # Check extensions status
```

**Use Case: Troubleshooting**
```bash
# Check what's installed
make status               # Overall Python setup status
make gnome-status         # Scripts/actions status for all file managers
make gnome-ext-status     # Python extensions status for all file managers

# Reinstall if broken
make gnome-uninstall && make gnome-install
make gnome-ext-uninstall && make gnome-ext-install
```

### Daily Usage Examples

**Basic File Operations:**
1. **Publish File**: Right-click file → YaDisk → "Publish (COM)" or "Publish (RU)"
2. **Copy to Stream**: Right-click file → YaDisk → "Copy to Stream"  
3. **Save Clipboard**: Right-click anywhere → YaDisk → "Save Clipboard"

**Batch Operations (Python Version):**
- Select multiple files → Right-click → YaDisk → Choose action
- Intelligent error handling continues with remaining files if some fail

**Menu Actions Available:**
| Action | Description | Location |
|--------|-------------|----------|
| **Publish (COM)** | Create public .com link and copy to clipboard | All file managers |
| **Publish (RU)** | Create public .ru link and copy to clipboard | All file managers |
| **Save Clipboard** | Save clipboard content to stream directory | Background click |
| **Save & Publish Clipboard** | Save clipboard and create public link | Background click |
| **Copy to Stream** | Copy selected files to stream directory | Selected files |
| **Move to Stream** | Move selected files to stream directory | Selected files |
| **Unpublish** | Remove public link for file | Single file |
| **Unpublish All Copies** | Remove public links for file and all copies | Single file |

## 🛠️ Troubleshooting

### Menu Not Appearing

**KDE Dolphin:**
```bash
# Check service menu files
ls ~/.local/share/kservices5/ServiceMenus/ydpublish*.desktop

# Restart Dolphin
dolphin --replace &
```

**GNOME Files:**
```bash
# Check scripts installation
ls ~/.local/share/nautilus/scripts/YaDisk*

# Restart Nautilus
nautilus -q
```

**Other File Managers:**
```bash
# Check status for all
make gnome-status
make thunar-status

# Verify dependencies
make install-system-deps
```

### Python Version Issues

**Virtual Environment:**
```bash
# Recreate if corrupted
rm -rf venv
make install

# Check Python wrapper
ls -la ydmenu-py-env
which ydmenu-py-env
```

**Dependencies:**
```bash
# Check system dependencies
python setup.py --check-deps

# Reinstall if needed
make clean && make install
```

### Environment Variables

**Check Setup:**
```bash
# Verify variables
echo $YA_DISK_ROOT
echo $YADISK_MENU_VERSION

# Check .env file (Python version)
cat .env
```

**Reset Environment:**
```bash
# Shell version
sudo nano /etc/environment

# Python version  
./setup.py  # Reconfigure
```

### Permission Issues

**Fix Permissions:**
```bash
# Make scripts executable
chmod +x ydmenu.py ydmenu.sh ydmenu-py-env

# Fix desktop files
chmod +x *.desktop

# GNOME scripts
chmod +x gnome/scripts/*
```

### Yandex Disk Issues

**Service Status:**
```bash
# Check daemon
yandex-disk status

# Restart if needed
yandex-disk stop
yandex-disk start

# Check logs
tail -f ~/.yandex-disk.log
```

## 📊 Status & Maintenance

### Check Installation Status
```bash
make status          # Overall status
make gnome-status    # GNOME file managers
make thunar-status   # Thunar status
```

### Update/Reinstall
```bash
# Update dependencies
make install-system-deps

# Reinstall Python version
make clean && make install && make configure

# Update desktop integration
make desktop-aware-install
```

### Uninstall
```bash
# Remove Python version
make uninstall

# Remove GNOME integration
make gnome-uninstall
make gnome-ext-uninstall

# Remove Thunar integration
make thunar-uninstall
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


## 🔗 Related Documentation

- **[Main README](../README.md)** - Project overview and quick start
- **[Python README](README_Python.md)** - Python version technical details
- **[Desktop Context Limitations](additional/DESKTOP_CONTEXT_LIMITATIONS.md)** - Known limitations
- **[Session Improvements](additional/SESSION_IMPROVEMENTS.md)** - X11/Wayland enhancements
- **[Migration Summary](additional/MIGRATION_SUMMARY.md)** - Shell to Python migration details
