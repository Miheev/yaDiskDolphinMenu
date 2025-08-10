# Yandex Disk Menu - Usage Guide & Examples

This guide provides detailed installation examples, file manager-specific setup, and troubleshooting instructions.

> **📋 Overview**: For project introduction and quick start, see [README](../README.md). For Python technical details, see [Python README](README_Python.md).

## 🖥️ File Manager-Specific Installation

### KDE Dolphin (Primary Support)

**Automated Installation:**
```bash
make install-system-deps  # Install KDE dependencies (kdialog, clipboard tools)
make install && make configure  # Python version with service menus
```

**Manual Setup:**
```bash
# Shell version only
./setup.sh

# Verify installation
ls ~/.local/share/kservices5/ServiceMenus/ydpublish*.desktop
```

**Menu Location:** Right-click on files → "YaDisk" or "YaDisk (Python)"

---

### GNOME Nautilus (Files) [Beta]

**Automated Installation:**
```bash
# Install GNOME dependencies
make install-system-deps  # Installs libnotify-bin, python3-nautilus, etc.

# Install with scripts
make install && make configure  # Desktop-aware; installs scripts automatically

# Optional: Install Python extension (enhanced integration)
make gnome-ext-install  # Requires python3-nautilus
```

**Manual Setup:**
```bash
# Scripts only (basic integration)
make gnome-install
nautilus -q  # Restart Files

# Python extension (advanced integration)
sudo apt install python3-nautilus python3-gi  # Ubuntu/Debian
make gnome-ext-install
nautilus -q
```

**Menu Locations:**
- **Scripts**: Files → Scripts → "YaDisk – ..."
- **Extension**: Right-click context menu → "YaDisk"

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

## 🔧 Installation Options Comparison

| Method | Speed | Features | When to Use |
|--------|-------|----------|-------------|
| **Desktop-aware** (`make configure`) | Fast | Auto-detects your file manager | **Recommended** - One command setup |
| **Shell only** (`./setup.sh`) | Fastest | Basic features, minimal deps | Lightweight systems, KDE only |
| **Manual install** | Slower | Full control over components | Troubleshooting, custom setups |

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

## 🎯 Usage Examples

### Basic File Operations
1. **Publish File**: Right-click file → YaDisk → "Publish (COM)" or "Publish (RU)"
2. **Copy to Stream**: Right-click file → YaDisk → "Copy to Stream"
3. **Save Clipboard**: Right-click anywhere → YaDisk → "Save Clipboard"

### Batch Operations (Python Version)
- Select multiple files → Right-click → YaDisk → Choose action
- Intelligent error handling continues with remaining files if some fail

### Menu Actions Available
| Action | Description |
|--------|-------------|
| **Publish (COM)** | Create public .com link and copy to clipboard |
| **Publish (RU)** | Create public .ru link and copy to clipboard |
| **Save Clipboard** | Save clipboard content to stream directory |
| **Save & Publish Clipboard** | Save clipboard and create public link |
| **Copy to Stream** | Copy selected files to stream directory |
| **Move to Stream** | Move selected files to stream directory |
| **Unpublish** | Remove public link for file |
| **Unpublish All Copies** | Remove public links for file and all copies |

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

## 🔗 Related Documentation

- **[Main README](../README.md)** - Project overview and quick start
- **[Python README](README_Python.md)** - Python version technical details
- **[Desktop Context Limitations](additional/DESKTOP_CONTEXT_LIMITATIONS.md)** - Known limitations
- **[Session Improvements](additional/SESSION_IMPROVEMENTS.md)** - X11/Wayland enhancements
- **[Migration Summary](additional/MIGRATION_SUMMARY.md)** - Shell to Python migration details
