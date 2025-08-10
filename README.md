# Yandex Disk Dolphin Menu

**Documentation:**
- [Python Version README](doc/README_Python.md)
- [Desktop Context Limitations](doc/DESKTOP_CONTEXT_LIMITATIONS.md)
- [Migration Notes](doc/MIGRATION_SUMMARY.md)
- [Usage Guide](doc/USAGE_GUIDE.md)

> **Note:** The Python version is the recommended implementation. A lightweight GNOME (Files 48+) integration is provided via Nautilus Scripts, with optional Nemo/Caja actions.
### Yandex Disk integration for KDE Dolphin sub menu: use yandex cloud directory for sharing clipboard content and files between PC, mobile, people, etc..

Inspired by [yandex disk indicator](https://github.com/slytomcat/yandex-disk-indicator/wiki/Yandex-disk-indicator) context menu options

### Menu v1.6.4
![Menu v1.6.4](https://raw.githubusercontent.com/Miheev/yaDiskDolphinMenu/main/doc/menu-v1.6.4-42.png)
### Overview
![Overview](https://raw.githubusercontent.com/Miheev/yaDiskDolphinMenu/main/doc/main-mix.png)

## Features:

Let's assume some directory under yandex cloud selected as **inbox** for **file stream**. It can be used as **destination** **for**: 
- Publish files
- Copy & Move files
- Save & Publish clipboard content (text & images)
- Screenshots captured via default KDE tool like [spectacle](https://apps.kde.org/ru/spectacle/) can be copied to clipboard and then saved to cloud via context menu
- Save clipboard content (without publishing)

**Pros** comparing to standard yd-tools menu items
- More resilient behavior: doesn't fail silently if __yandex-disk__ service busy or unavailable, **wait 30s for idle status** and shows notifications accordingly
- Separate menu group
- **Non-blocking** native **notifications** (kdialog)
- Show published links in notification as **clicable links**
- Show **both published links**: for COM domain (EN language) RU domain (RU language)
- Separate menu options for capturing appropriate link (RU, EN) to clipboard (2 links present in notification anyway)
- Add a **label** to **filename**, if file created from **clipboard** (datetime + cleaned 30 chars from note)
- Doesn't fail on overwrite: **rename automatically** instead (__%name%\_%number%.%extension% or .%extensionName%\_%number%__)
- **Unpublish** file with its **copies** (if copies created with patterns above)
- **Unpublish file outside** of cloud directories (instead of throwing error, unpublish its copy from the inbox directory)
- **Multiple item processing**: Select multiple files/directories in Dolphin for batch operations (Python version only)
- **Enhanced error handling**: Continue processing remaining items if some fail, with detailed error logging
- **Log output** to parent of yandex disk root directory (__$YA_DISK_ROOT/yaMedia.log__ for bash, __$YA_DISK_ROOT/yaMedia-python.log__ for Python) 

**Cons**
- EN localization supported only

**HINT**: Set up and use additional account for file synchronization and 3rd party services to prevent over sync and too broad access rights sharing.  
Set up shared directory access from primary to friendly account for such purpose.


## Requirements

### System Dependencies
- **yandex-disk**: Yandex Disk daemon
- **KDE/Dolphin**: KDE desktop environment with Dolphin file manager  
- **Python 3**: Python 3.6 or higher
- **python3-venv**: Virtual environment support
- **kdialog**: KDE dialog utility
- **Clipboard utilities**:
  - **xclip**: For X11 environments
  - **wl-clipboard**: For Wayland environments
- **Icons pack**: From [yd-tools](https://github.com/slytomcat/yandex-disk-indicator/doc/Yandex-disk-indicator) (after installation should be in /usr/share/yd-tools/icons)

Since current scripts created on top of yandex disk indicator, there is a good chance that it installs and set up some not listed dependencies.
I'd rather suggest to install it anyway.


### Tested on
- distributive: [KDE Neon](https://neon.kde.org/) 5.21 (Ubuntu + KDE)
- KDE: 5.21.4
- Linux core version: 5.4.0-72-generic
- bash: 5.0.17(1)-release (x86_64-pc-linux-gnu)


## Install & Setup

### System Dependencies Installation

Install system dependencies automatically based on your Linux distribution:
```bash
make install-system-deps  # Detects package manager and session type (X11/Wayland)
```

This will install:
- Python virtual environment support
- Appropriate clipboard tools (xclip for X11, wl-clipboard for Wayland)

### GNOME Integration (Files 48+) [Beta]

GNOME support is provided via Scripts-based integration (compatible with Nautilus/Files v48+). This integration is in beta and needs broader testing across distros and versions:

```bash
make gnome-install   # installs scripts via symlinks
make gnome-status    # shows installed scripts/actions
make gnome-uninstall # removes scripts/actions
make gnome-ext-install   # optional: install Nautilus python extension (python3-nautilus)
make gnome-ext-status    # check extension presence
make gnome-ext-uninstall # remove extension
```

- Menu location: Files → Scripts → "YaDisk – ..."
- Actions mirror Dolphin: Publish (COM/RU), Unpublish, Unpublish All Copies, Save Clipboard, Save & Publish Clipboard (COM/RU), Copy/Move to Stream
- Nemo/Caja: optional actions installed if file manager is detected
- Notifications: handled by core app (kdialog preferred; notify-send fallback)

Dependencies for GNOME environments:
- Clipboard: `wl-clipboard` (Wayland) or `xclip` (X11)
- Notifications: `libnotify-bin` (provides `notify-send`)
- Optional extensions: `python3-nautilus`, `python3-gi` (with GTK GIR)

### Basic Setup
- Install & configure [yandex-disk](https://yandex.com/support/disk-desktop-linux/) and [yd-tools](https://github.com/slytomcat/yandex-disk-indicator/wiki/Yandex-disk-indicator) as described in corresponding docs

### Setup via script
- Download repo to some permanent directory 
- Set up variables inside ``setup.sh`` script as described there
- Run ``setup.sh`` script  
It creates scripts symlinks instead of copies (manual setup example)

### Manual setup
- Download repo to somewhere
- Set up environment variables, simple path without whitespaces expected   
    - $YA_DISK_ROOT path: parent of yandex disk root directory, e.g. __$HOME/Public__ 
    Set global static var (local in .bash_profile and .bashrc doesn't work for me)  
``sudo echo "YA_DISK_ROOT=$HOME/Public" >> /etc/environment``
    - set yandex disk root directory and inbox directory under the root, e.g. __$YA_DISK_ROOT/yaDisk__ and __$YA_DISK_ROOT/yaDisk/fileInbox__ respectively  
     Thus parameters can be found in ``./ydmenu.sh`` under line 23:  __yaDisk__ and __streamDir__
- Run commands inside of repo root
    - make default config backup  
``mv $HOME/.local/share/kservices5/ServiceMenus/ydpublish.desktop $HOME/.local/share/kservices5/ServiceMenus/ydpublish.desktop.bak``
    - copy new desktop menu spec  
``cp ./ydpublish.desktop ~/.local/share/kservices5/ServiceMenus``
    - copy script to local bin dir
``cp ./ydmenu.sh ~/bin``
- Make sure ydpublish.desktop and ydmenu.sh are executable

### Finish setup
- Logout & login
 - Now __YaDisk__ menu group should be available in Dolphin; in GNOME Files, see Scripts submenu
- Enjoy!
- Reconfigure via script or manually if needed

## Technical Details

### Clipboard Compatibility
The Python version uses **pyclip** for clipboard operations, which automatically switches between:
- **xclip** on X11 environments
- **wl-clipboard** on Wayland environments

This provides seamless cross-platform clipboard support without manual configuration.

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

### Automated Releases

- Workflow: `.github/workflows/release.yml`
- Manual trigger: GitHub → Actions → Release → Run workflow → provide `version` (e.g., `1.5.3`, `2.0.0-RC1`)
- What happens:
  - Runs `update_version.sh <version>` to update `.env`, regenerate desktop files, commit, tag `v<version>`, and push
  - Creates a GitHub Release with autogenerated notes
- Tag push trigger: Pushing a tag like `v1.5.3` also creates a Release with notes based on commits since the previous tag
