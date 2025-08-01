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

The setup process involves:
1. Configure variables in `setup.sh`:
   - `YA_DISK_ROOT` - Parent directory of Yandex disk (e.g., `$HOME/Public`)
   - `YA_DISK_RELATIVE` - Yandex disk directory name (e.g., `yaDisk`)
   - `INBOX_RELATIVE` - Inbox directory for file stream (e.g., `Media`)
2. Run `./setup.sh` to set global environment variables and create symlinks
3. The script modifies `/etc/environment` and creates symlinks in KDE service menu directories

## Dependencies & Requirements

- KDE Linux with Dolphin file manager
- `yandex-disk` daemon installed and running
- `yd-tools` icon pack (icons in `/usr/share/yd-tools/icons/`)
- Standard Linux utilities: `kdialog`, `awk`, `xclip`, `grep`, `cut`, `iconv`

## Core Functionality

The main script (`ydmenu.sh`) handles:
- **Publishing**: Create public links for files (both .com and .ru domains)
- **Clipboard operations**: Save/publish clipboard content (text and images)
- **File management**: Copy/move files to Yandex stream directory
- **Unpublishing**: Remove public links for files and their copies
- **Error handling**: Wait for yandex-disk service readiness, show notifications
- **File naming**: Auto-rename duplicates with `_number` suffix pattern

## Configuration Variables

Runtime configuration is done through these variables in `ydmenu.sh`:
- `yaDisk` - Path to Yandex disk root directory
- `streamDir` - Path to inbox/stream directory for file operations
- `logFilePath` - Path to log file for operations

All operations are logged to `$YA_DISK_ROOT/yaMedia.log`.