#!/usr/bin/env python3
"""
Yandex Disk menu actions logic for KDE Dolphin
Python rewrite of ydmenu.sh functionality
"""

import os
import sys
import re
import subprocess
import time
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple, List
import tempfile
import logging

try:
    import pyclip
    PYCLIP_AVAILABLE = True
except ImportError:
    PYCLIP_AVAILABLE = False


class Constants:
    """Centralized constants for the YaDisk menu application"""
    
    # Service Menu Files (Python version only, shell version deprecated)
    SERVICE_MENU_FILES = ('ydpublish-python.desktop',)
    
    @staticmethod
    def get_service_menu_filenames():
        """Get filenames of KDE service menu files to filter out"""
        return [
            "ydpublish-python.desktop"
        ]
    
    # Command Categories
    ONE_BY_ONE_COMMANDS = ('PublishToYandexCom', 'PublishToYandex', 'UnpublishFromYandex', 'UnpublishAllCopy')
    ALL_AT_ONCE_COMMANDS = ('FileAddToStream', 'FileMoveToStream')
    CLIPBOARD_COMMANDS = ('ClipboardPublishToCom', 'ClipboardPublish', 'ClipboardToStream')
    
    # Paths and Directories
    ICON_BASE_PATH = '/usr/share/yd-tools/icons'
    YANDEX_DISK_DIR = 'yaMedia'
    STREAM_DIR = 'Media'
    LOG_FILE_NAME = 'yaMedia-python.log'
    NOTE_FILE_PREFIX = 'note-'
    KDE_SERVICE_MENU_PATH = '.local/share/kservices5/ServiceMenus'
    
    # File Extensions
    DEFAULT_IMAGE_EXT = 'png'
    DEFAULT_TEXT_EXT = 'txt'
    
    # URLs
    YANDEX_DISK_URL_BASE = 'https://disk.yandex.com'
    YANDEX_SHORT_URL_MARKER = '.sk'
    
    # Icons
    ICONS = {
        'info': f'{ICON_BASE_PATH}/yd-128.png',
        'warn': f'{ICON_BASE_PATH}/yd-128_g.png', 
        'error': f'{ICON_BASE_PATH}/light/yd-ind-error.png'
    }
    
    # Image Signatures
    IMAGE_SIGNATURES = {
        b'\x89PNG\r\n\x1a\n': 'png',
        b'\xff\xd8\xff': 'jpg',
        b'GIF87a': 'gif',
        b'GIF89a': 'gif',
        b'\x42\x4d': 'bmp'
    }
    
    # Application Settings
    TITLE = 'Yandex.Disk'
    WAIT_TIMEOUT = 30
    
    # Timeouts
    TIMEOUT_SHORT = 5
    TIMEOUT_MEDIUM = 10
    TIMEOUT_LONG = 30
    TIMEOUT_SYNC = 60
    TIMEOUT_ERROR = 15
    SLEEP_INTERVAL = 1
    
    # Text Processing
    UUID_HEX_LENGTH = 8
    TEXT_SUMMARY_LENGTH = 30
    EXIT_CODE_ERROR = 1
    
    # Array Indices
    DEFAULT_INDEX = 0
    SPLIT_INDEX_LAST = -1
    FIRST_LINE_INDEX = 0
    INCREMENT_STEP = 1


class ClipboardHandler:
    """Simplified clipboard handler using pyclip as primary with xclip fallback"""
    
    def __init__(self, logger):
        self.logger = logger
    
    def get_text(self) -> Optional[str]:
        """Get text from clipboard using pyclip as primary"""
        if PYCLIP_AVAILABLE:
            try:
                content = pyclip.paste(text=True)
                # Handle both string and bytes return types
                if content:
                    if isinstance(content, bytes):
                        content = content.decode('utf-8', errors='ignore')
                    self.logger.debug("Retrieved text content from clipboard using pyclip")
                    return content
            except Exception as e:
                self.logger.warning(f"pyclip failed: {e}")
        
        # pyclip not available or failed - return None for xclip fallback
        return None
    
    def set_text(self, text: str) -> bool:
        """Set text to clipboard using pyclip as primary"""
        if PYCLIP_AVAILABLE:
            try:
                pyclip.copy(text)
                self.logger.debug(f"Copied to clipboard using pyclip: {text}")
                return True
            except Exception as e:
                self.logger.warning(f"pyclip failed: {e}")
        
        # pyclip not available or failed - return False for xclip fallback
        return False
    
    def has_image(self) -> bool:
        """Check if clipboard contains image data using pyclip"""
        if PYCLIP_AVAILABLE:
            try:
                # Try to get binary data from clipboard
                data = pyclip.paste()
                if data and isinstance(data, bytes):
                    # Check if it looks like image data using signature constants
                    # Note: We need to access constants from YandexDiskMenu class
                    signatures = Constants.IMAGE_SIGNATURES
                    if any(data.startswith(sig) for sig in signatures.keys()):
                        self.logger.debug("Clipboard contains image data (detected via pyclip)")
                        return True
                return False
            except Exception as e:
                self.logger.debug(f"pyclip image check failed: {e}")
        
        return False
    
    def get_image_data(self) -> Optional[bytes]:
        """Get image data from clipboard using pyclip"""
        if PYCLIP_AVAILABLE:
            try:
                data = pyclip.paste()
                if data and isinstance(data, bytes):
                    self.logger.debug("Retrieved image data from clipboard using pyclip")
                    return data
            except Exception as e:
                self.logger.debug(f"pyclip image retrieval failed: {e}")
        return None


class YandexDiskMenu:
    """Main class for Yandex Disk menu operations"""
    
    def __init__(self, verbose: bool = False):
        # Get environment variables
        self.ya_disk_root = os.environ.get('YA_DISK_ROOT', f"{os.path.expanduser('~')}/Public")
        self.ya_disk = f"{self.ya_disk_root}/{Constants.YANDEX_DISK_DIR}"
        self.stream_dir = f"{self.ya_disk}/{Constants.STREAM_DIR}"
        self.log_file_path = f"{self.ya_disk_root}/{Constants.LOG_FILE_NAME}"
        self.verbose = verbose
        
        self.start_time = time.time()
        
        # Setup logging with verbosity control
        # Use a unique logger name to avoid handler duplication across instances
        import uuid
        logger_name = f'YandexDiskMenu_{uuid.uuid4().hex[:Constants.UUID_HEX_LENGTH]}'
        self.logger = logging.getLogger(logger_name)
        
        # Set log level based on verbosity
        log_level = logging.DEBUG if verbose else logging.INFO
        self.logger.setLevel(log_level)
        
        # Clear any existing handlers (shouldn't be needed with unique names, but safety first)
        self.logger.handlers.clear()
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # File handler (always INFO level for file)
        file_handler = logging.FileHandler(self.log_file_path)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # Console handler (respects verbosity)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # Prevent propagation to root logger
        self.logger.propagate = False
        
        # Initialize clipboard handler
        self.clipboard = ClipboardHandler(self.logger)
    
    def __del__(self):
        """Cleanup logger handlers to prevent resource warnings"""
        try:
            for handler in self.logger.handlers[:]:
                handler.close()
                self.logger.removeHandler(handler)
        except:
            pass
        
    def log_message(self, message: str, level: str = 'info') -> None:
        """Log message using logging module with specified level"""
        getattr(self.logger, level.lower())(message)
            
    def format_file_path(self, file_path: str) -> str:
        """Format file path for display - make file name bold"""
        if not file_path:
            return ""
        file_name = os.path.basename(file_path)
        return f"<b>{file_name}</b>"
    
    def format_link(self, url: str) -> str:
        """Format URL as clickable link"""
        if not url:
            return ""
        return f"<a href='{url}'><b>{url}</b></a>"
            
    def show_notification(self, message: str, timeout: int = None, icon_type: str = 'info') -> None:
        """Show KDE notification using kdialog"""
        if timeout is None:
            timeout = Constants.TIMEOUT_SHORT
        icon = Constants.ICONS.get(icon_type, Constants.ICONS['info'])
        elapsed_time = int(time.time() - self.start_time)
        full_message = f"{message}\nTime: {elapsed_time}s"
        
        try:
            subprocess.run([
                'kdialog', '--icon', icon, '--title', Constants.TITLE,
                '--passivepopup', full_message, str(timeout)
            ], check=False, timeout=Constants.TIMEOUT_MEDIUM)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            # Fallback to logging if kdialog not available or times out
            self.logger.warning(f"NOTIFICATION: {full_message}")
        
        self.logger.info(message)
    
    def show_error_and_exit(self, message: str, log_message: str = None) -> None:
        """Show error notification and exit"""
        error_msg = log_message or message
        self.logger.error(error_msg)
            
        notification_msg = f"{message}\nSee <a href='file://{self.log_file_path}'>log</a> for details"
        self.show_notification(notification_msg, Constants.TIMEOUT_ERROR, 'error')
        sys.exit(Constants.EXIT_CODE_ERROR)
    
    def _run_command(self, cmd: List[str], timeout: int = None, check: bool = True, input: str = None) -> subprocess.CompletedProcess:
        """Helper method to run subprocess commands with consistent error handling and logging"""
        timeout = timeout or Constants.TIMEOUT_LONG
        self.logger.debug(f"Running command: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=check, input=input)
            
            # Log stdout and stderr
            if result.stdout:
                # Only log stdout when in verbose mode
                if self.verbose:
                    self.logger.info(f"Command stdout: {result.stdout.strip()}")
            if result.stderr:
                # Always log stderr regardless of verbose setting
                self.logger.warning(f"Command stderr: {result.stderr.strip()}")
            
            self.logger.debug(f"Command completed with return code: {result.returncode}")
            return result
            
        except subprocess.TimeoutExpired as e:
            self.logger.error(f"Command timed out after {timeout}s: {' '.join(cmd)}")
            raise subprocess.CalledProcessError(Constants.EXIT_CODE_ERROR, cmd, f"Command timed out after {timeout}s")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Command failed: {' '.join(cmd)}, Return code: {e.returncode}")
            if e.stdout:
                self.logger.error(f"Command stdout: {e.stdout.strip()}")
            if e.stderr:
                self.logger.error(f"Command stderr: {e.stderr.strip()}")
            raise
    
    def _parse_yandex_status(self, stdout: str) -> str:
        """Parse yandex-disk status output to extract status code"""
        status_line = next((line for line in stdout.split('\n') 
                          if 'status:' in line.lower()), '')
        return status_line.split(':', Constants.SPLIT_INDEX_LAST)[Constants.SPLIT_INDEX_LAST].strip() if ':' in status_line else 'not started'
    
    def _get_yandex_status(self, timeout: int = None) -> str:
        """Get current yandex-disk status"""
        timeout = timeout or Constants.TIMEOUT_MEDIUM
        try:
            result = self._run_command(['yandex-disk', 'status'], timeout=timeout, check=False)
            return self._parse_yandex_status(result.stdout)
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            self.logger.warning("Failed to get yandex-disk status")
            return 'not started'
    
    def wait_for_ready(self) -> None:
        """Wait for yandex-disk daemon to be ready"""
        status_code = self._get_yandex_status()
        if status_code == 'idle':
            return
        
        self.show_notification(f"<b>Service status: {status_code}</b>.\nWill wait for <b>{Constants.WAIT_TIMEOUT}s</b> and exit if no luck.", 
                             Constants.TIMEOUT_ERROR, 'warn')
        
        for i in range(Constants.WAIT_TIMEOUT):
            status_code = self._get_yandex_status(timeout=Constants.TIMEOUT_SHORT)
            if status_code == 'idle':
                self.logger.debug(f"Yandex-disk ready after {i+Constants.INCREMENT_STEP} seconds")
                return
            time.sleep(Constants.SLEEP_INTERVAL)
            
        self.show_error_and_exit(
            "<b>Service is not available</b>.\nTry later or restart it via\n<b><i>yandex-disk stop && yandex-disk start</i></b>.",
            "Service is not available"
        )
    
    def _get_clipboard_image_type(self) -> Optional[str]:
        """Check if clipboard contains image using native Python libraries with xclip fallback"""
        # Try pyclip first
        if self.clipboard.has_image():
            return "image/png"  # Default to PNG for pyclip
        
        # Fall back to xclip for detailed image type detection
        try:
            result = self._run_command(['xclip', '-selection', 'clipboard', '-t', 'TARGETS', '-o'], 
                                     timeout=Constants.TIMEOUT_SHORT, check=False)
            return next((line.strip() for line in result.stdout.split('\n') 
                        if line.strip().startswith('image')), None)
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.logger.debug("xclip not available or no image in clipboard")
            return None
    
    def _save_clipboard_image(self, target_type: str, current_date: str) -> str:
        """Save clipboard image to file using native Python libraries with xclip fallback"""
        extension = target_type.split('/')[Constants.SPLIT_INDEX_LAST] if '/' in target_type else Constants.DEFAULT_IMAGE_EXT
        full_path = f"{self.stream_dir}/{Constants.NOTE_FILE_PREFIX}{current_date}.{extension}"
        
        # Try pyclip first
        image_data = self.clipboard.get_image_data()
        if image_data:
            try:
                with open(full_path, 'wb') as f:
                    f.write(image_data)
                self.logger.info(f"Saved clipboard image to: {full_path}")
                return full_path
            except IOError as e:
                self.logger.warning(f"Failed to save image data from pyclip: {e}")
        
        # Fall back to xclip
        try:
            with open(full_path, 'wb') as f:
                subprocess.run(['xclip', '-selection', 'clipboard', '-t', target_type, '-o'],
                              stdout=f, check=True)
            
            self.logger.info(f"Saved clipboard image to: {full_path} (using xclip fallback)")
            return full_path
        except (subprocess.CalledProcessError, FileNotFoundError, IOError) as e:
            self.show_error_and_exit(f"Failed to save clipboard image: {e}")
            return ""
    
    def _get_clipboard_text(self) -> str:
        """Get text content from clipboard using native Python libraries with xclip fallback"""
        # Try pyclip first
        content = self.clipboard.get_text()
        if content:
            return content
        
        # Fall back to xclip
        try:
            result = self._run_command(['xclip', '-selection', 'clipboard', '-o'], timeout=Constants.TIMEOUT_SHORT)
            self.logger.debug("Retrieved text content from clipboard using xclip fallback")
            return result.stdout
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.show_error_and_exit("Cannot access clipboard - all methods failed")
            return ""
    
    def _create_filename_from_text(self, content: str, current_date: str) -> str:
        """Create sanitized filename from text content"""
        name_summary = ''
        if content.strip():
            first_line = content.split('\n')[Constants.FIRST_LINE_INDEX][:Constants.TEXT_SUMMARY_LENGTH]
            # Remove problematic characters
            name_summary = re.sub(r'[<>|\\;/(),"\']|(https?:)|(:)|( {2})|( \.)+$', '', first_line).strip()
            if name_summary:
                name_summary = f" {name_summary}"
        
        return f"{self.stream_dir}/{Constants.NOTE_FILE_PREFIX}{current_date}{name_summary}.{Constants.DEFAULT_TEXT_EXT}"
    
    def get_clipboard_content(self) -> Optional[str]:
        """Get clipboard content using pyclip with xclip fallback"""
        try:
            current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Check for image content first
            target_type = self._get_clipboard_image_type()
            if target_type:
                self.logger.debug(f"Clipboard contains image: {target_type}")
                return self._save_clipboard_image(target_type, current_date)
            
            # Get text content
            content = self._get_clipboard_text()
            if not content or not content.strip():
                self.logger.warning("Clipboard is empty or contains only whitespace")
                return None
            
            # Save text to file
            full_path = self._create_filename_from_text(content, current_date)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.logger.info(f"Saved clipboard text to: {full_path}")
            return full_path
            
        except (IOError, OSError) as e:
            self.show_error_and_exit(f"Save clipboard error: {e}")
    
    def _copy_to_clipboard(self, text: str) -> None:
        """Copy text to clipboard using native Python libraries with xclip fallback"""
        # Try pyclip first
        if self.clipboard.set_text(text):
            return
        
        # Fall back to xclip
        try:
            self._run_command(['xclip', '-selection', 'clipboard'], 
                            timeout=Constants.TIMEOUT_SHORT, check=True, input=text)
            self.logger.debug(f"Copied to clipboard using xclip fallback: {text}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.show_error_and_exit("Cannot copy to clipboard - all methods failed")
    
    def _create_com_link(self, publish_path: str) -> str:
        """Convert .ru link to .com domain"""
        return f"{Constants.YANDEX_DISK_URL_BASE}{publish_path.split(Constants.YANDEX_SHORT_URL_MARKER, Constants.INCREMENT_STEP)[Constants.SPLIT_INDEX_LAST]}" if Constants.YANDEX_SHORT_URL_MARKER in publish_path else publish_path
    
    def _validate_publish_result(self, publish_path: str) -> None:
        """Validate yandex-disk publish result for errors"""
        error_indicators = ['unknown publish error', 'unknown error', 'error:']
        if any(error in publish_path.lower() for error in error_indicators):
            self.show_error_and_exit(f"<b>{publish_path}</b>", publish_path)
    
    def publish_file(self, file_path: str, use_com_domain: bool = True) -> None:
        """Publish file and copy link to clipboard"""
        try:
            result = self._run_command(['yandex-disk', 'publish', file_path], timeout=Constants.TIMEOUT_LONG)
            publish_path = result.stdout.strip()
            
            self._validate_publish_result(publish_path)
            com_link = self._create_com_link(publish_path)
            
            self.logger.info(file_path)
            self.logger.info(publish_path)
            self.logger.info(com_link)
            
            # Show notification with formatted links
            file_display = self.format_file_path(file_path)
            com_link_display = self.format_link(com_link)
            ru_link_display = self.format_link(publish_path)
            
            if use_com_domain:                
                self._copy_to_clipboard(com_link)
                message = (f"Published {file_display} (.com link copied):\n"
                          f"{com_link_display}\n"
                          f"Alternative: {ru_link_display}")
            else:
                self._copy_to_clipboard(publish_path)
                message = (f"Published {file_display} (.ru link copied):\n"
                          f"{ru_link_display}\n"
                          f"Alternative: {com_link_display}")
            
            self.show_notification(message, Constants.TIMEOUT_MEDIUM)
            
        except subprocess.CalledProcessError as e:
            self.show_error_and_exit(f"Publish error: {e}")
    
    def unpublish_file(self, file_path: str) -> str:
        """Unpublish a single file"""
        try:
            result = self._run_command(['yandex-disk', 'unpublish', file_path], timeout=Constants.TIMEOUT_LONG)
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            return f"Error: {e}"
    
    def unpublish_copies(self, base_dir: str, base_file: str, file_name: str) -> str:
        """Unpublish file and all its numbered copies"""
        file_path = Path(base_file)
        name_part = file_path.stem
        ext_part = file_path.suffix
        
        # Handle hidden files
        if file_name.startswith('.'):
            name_part = file_name
            ext_part = ''
        
        results = []
        index = Constants.DEFAULT_INDEX
        
        while True:
            if index == Constants.DEFAULT_INDEX:
                current_file = base_file
                current_name = file_name
            else:
                current_name = f"{name_part}_{index}{ext_part}"
                current_file = f"{base_dir}/{current_name}"
            
            if not os.path.exists(current_file):
                break
                
            result = self.unpublish_file(current_file)
            results.append(f"<b>{current_name}</b> - {result}")
            
            index += Constants.INCREMENT_STEP
        
        return ';\n'.join(results)
    
    def sync_yandex_disk(self) -> str:
        """Trigger yandex-disk sync"""
        try:
            result = self._run_command(['yandex-disk', 'sync'], timeout=Constants.TIMEOUT_SYNC)
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            return f"Sync error: {e}"
    
    def generate_unique_filename(self, target_dir: str, filename: str) -> str:
        """Generate unique filename by adding _N suffix if file exists"""
        file_path = Path(filename)
        name_part = file_path.stem
        ext_part = file_path.suffix
        
        # Handle hidden files
        if filename.startswith('.'):
            name_part = filename
            ext_part = ''
        
        index = Constants.DEFAULT_INDEX
        while True:
            if index == Constants.DEFAULT_INDEX:
                new_filename = filename
            else:
                new_filename = f"{name_part}_{index}{ext_part}"
            
            ya_disk_path = f"{self.ya_disk}/{new_filename}"
            stream_path = f"{self.stream_dir}/{new_filename}"
            target_path = f"{target_dir}/{new_filename}"
            
            if not any(os.path.exists(p) for p in [ya_disk_path, stream_path, target_path]):
                return new_filename
                
            index += Constants.INCREMENT_STEP
    
    def _parse_file_info(self, file_path: str) -> Tuple[str, str, str, bool]:
        """Parse file path information and determine if file is outside ya_disk"""
        file_name = os.path.basename(file_path) if file_path else ''
        file_dir = os.path.dirname(file_path) if file_path else ''
        is_outside_file = not file_path.startswith(f"{self.ya_disk}/") if file_path else True
        return file_path, file_name, file_dir, is_outside_file
    
    def _should_rename_file(self, file_path: str, file_name: str, is_outside_file: bool, command_type: str) -> bool:
        """Check if file needs renaming to avoid conflicts"""
        if not file_path or not os.path.exists(file_path):
            return False
            
        # Only rename if there's an actual conflict with existing files
        stream_file_path = f"{self.stream_dir}/{file_name}"
        ya_disk_file_path = f"{self.ya_disk}/{file_name}"
        
        has_conflict = os.path.exists(stream_file_path) or os.path.exists(ya_disk_file_path)
        
        # Only rename if we have a conflict AND it's a scenario where renaming makes sense
        needs_rename = ((is_outside_file and command_type.startswith('PublishToYandex')) or 
                       command_type.startswith('File'))
        
        # Key fix: Only rename if there's BOTH a conflict AND a need to rename
        return has_conflict and needs_rename
    
    def _generate_unique_file_name(self, file_path: str, file_name: str, file_dir: str) -> Tuple[str, str]:
        """Generate unique filename to avoid conflicts"""
        file_path_obj = Path(file_path)
        
        if file_name.startswith('.'):
            # Hidden file
            file_name_part = file_name
            ext_part = ''
        else:
            # Regular file
            file_name_part = file_path_obj.stem
            ext_part = file_path_obj.suffix
        
        index = Constants.DEFAULT_INDEX
        while True:
            index += Constants.INCREMENT_STEP
            new_file_name = f"{file_name_part}_{index}{ext_part}"
            new_stream_path = f"{self.stream_dir}/{new_file_name}"
            new_ya_disk_path = f"{self.ya_disk}/{new_file_name}"
            new_src_path = f"{file_dir}/{new_file_name}"
            
            if (not os.path.exists(new_stream_path) and 
                not os.path.exists(new_ya_disk_path) and 
                not os.path.exists(new_src_path)):
                return new_file_name, f"{file_dir}/{new_file_name}"
    
    def _rename_file_if_needed(self, file_path: str, file_name: str, file_dir: str, 
                              is_outside_file: bool, command_type: str) -> Tuple[str, str, bool]:
        """Rename file if needed to avoid conflicts, return updated values"""
        if not self._should_rename_file(file_path, file_name, is_outside_file, command_type):
            return file_path, file_name, False
        
        new_file_name, new_src_file_path = self._generate_unique_file_name(file_path, file_name, file_dir)
        
        self.logger.info(f"Renaming source file: {file_path} -> {new_src_file_path}")
        shutil.move(file_path, new_src_file_path)
        
        return new_src_file_path, new_file_name, True
    
    def _create_rename_back_function(self, is_file_name_changed: bool, src_file_path: str, original_src_file_path: str):
        """Create a function to rename file back to original name"""
        def rename_back():
            if is_file_name_changed and os.path.exists(src_file_path):
                self.logger.info(f"Renaming back: {src_file_path} -> {original_src_file_path}")
                shutil.move(src_file_path, original_src_file_path)
        return rename_back


def main_impl(command_type: str, file_paths: tuple = (), verbose: bool = False):
    """Yandex Disk menu actions for KDE Dolphin (now supports multiple files/dirs with different processing algorithms)"""
    yd_menu = YandexDiskMenu(verbose=verbose)
    
    # Filter out empty paths and KDE service menu desktop files
    # - Empty paths can come from %k/%c parameters when they're not set
    # - KDE service menu files come from %k parameter and must be excluded to prevent
    #   processing the menu definition file as a regular file
    # - Filter by filename ending (Python version only, since shell version is deprecated)
    service_menu_filenames = Constants.get_service_menu_filenames()
    filtered_file_paths = tuple(fp for fp in file_paths 
                               if fp and not any(fp.endswith(menu_file) for menu_file in service_menu_filenames))
    
    # Use filtered file paths for processing
    file_paths = filtered_file_paths
    
    # Log input parameters with INFO level
    yd_menu.logger.info(f"=== YDMENU INPUT PARAMETERS ===")
    yd_menu.logger.info(f"command_type: '{command_type}'")
    yd_menu.logger.info(f"file_paths: {file_paths}")
    yd_menu.logger.info(f"verbose: {verbose}")
    yd_menu.logger.info(f"file_paths count: {len(file_paths)}")
    yd_menu.logger.info(f"file_paths types: {[type(fp).__name__ for fp in file_paths]}")
    
    # Log file path details if any files are provided (verbose mode only)
    if file_paths and verbose:
        yd_menu.logger.debug("=== FILE PATH DETAILS ===")
        for i, file_path in enumerate(file_paths):
            yd_menu.logger.debug(f"file_path[{i}]: '{file_path}'")
            if os.path.exists(file_path):
                yd_menu.logger.debug(f"  - exists: True")
                yd_menu.logger.debug(f"  - is_file: {os.path.isfile(file_path)}")
                yd_menu.logger.debug(f"  - is_dir: {os.path.isdir(file_path)}")
                yd_menu.logger.debug(f"  - size: {os.path.getsize(file_path) if os.path.isfile(file_path) else 'N/A'}")
            else:
                yd_menu.logger.debug(f"  - exists: False")
    
    yd_menu.logger.info(f"Start - Command: {command_type}")
    yd_menu.wait_for_ready()

    if not file_paths:
        file_paths = ()

    # Create command processor and delegate all processing logic
    processor = CommandProcessor(yd_menu)
    processor.process_command(command_type, file_paths)
    yd_menu.logger.info("Done")





def _handle_publish_command_collect_link(yd_menu: YandexDiskMenu, command_type: str, src_file_path: str, 
                                       is_outside_file: bool, ya_disk_file_path: str) -> str:
    """Handle publish command and return the generated link instead of copying to clipboard"""
    use_com = command_type == 'PublishToYandexCom'
    
    # Store original clipboard content
    original_clipboard = None
    try:
        original_clipboard = yd_menu.clipboard.get_text()
    except:
        pass
    
    # Publish the file
    yd_menu.publish_file(src_file_path, use_com)
    
    # Get the published link from clipboard
    published_link = None
    try:
        published_link = yd_menu.clipboard.get_text()
    except:
        pass
    
    # Restore original clipboard content
    if original_clipboard:
        yd_menu._copy_to_clipboard(original_clipboard)
    
    # For outside files or directories, move to stream directory after publishing
    if is_outside_file:
        shutil.move(ya_disk_file_path, yd_menu.stream_dir)
    
    return published_link



def _handle_batch_add_to_stream(yd_menu: YandexDiskMenu, processed_items: list) -> None:
    """Handle batch copy to stream operation"""
    import errno
    copied_items = []
    errors = []
    
    for src_file_path, file_name, rename_back in processed_items:
        try:
            if os.path.isdir(src_file_path):
                base_name = os.path.basename(src_file_path.rstrip(os.sep))
                dest_dir = os.path.join(yd_menu.stream_dir, base_name)
                try:
                    shutil.copytree(src_file_path, dest_dir)
                    copied_items.append(f"Directory: {src_file_path}")
                except OSError as e:
                    if e.errno == errno.ENOTDIR:
                        shutil.copy2(src_file_path, dest_dir)
                        copied_items.append(f"File: {src_file_path}")
                    else:
                        raise
            else:
                shutil.copy2(src_file_path, yd_menu.stream_dir)
                copied_items.append(f"File: {src_file_path}")
            
            # Rename back for copy operations
            rename_back()
            
        except Exception as e:
            errors.append((src_file_path, str(e)))
            yd_menu.logger.error(f"Error copying {src_file_path}: {e}")
    
    sync_status = yd_menu.sync_yandex_disk()
    
    # Handle errors but don't exit - show what succeeded and what failed
    if errors and copied_items:
        # Some succeeded, some failed
        error_details = '\n'.join(f"<b>{os.path.basename(fp)}</b>: {err}" for fp, err in errors[:3])
        if len(errors) > 3:
            error_details += f"\n... and {len(errors) - 3} more errors"
        yd_menu.show_notification(f"Copied {len(copied_items)} items, {len(errors)} failed:\n{error_details}", 
                                 Constants.TIMEOUT_MEDIUM, 'warn')
    elif errors:
        # All failed
        error_details = '\n'.join(f"<b>{os.path.basename(fp)}</b>: {err}" for fp, err in errors[:3])
        if len(errors) > 3:
            error_details += f"\n... and {len(errors) - 3} more errors"
        yd_menu.show_notification(f"Copy failed for all items:\n{error_details}", Constants.TIMEOUT_ERROR, 'error')
        return
    
    # Create notification message showing first 5 items with count of remaining - format file names
    if len(copied_items) > 5:
        display_items = [item.replace("File: ", "").replace("Directory: ", "") for item in copied_items[:5]]
        formatted_items = [f"<b>{os.path.basename(item)}</b>" for item in display_items]
        remaining_count = len(copied_items) - 5
        display_message = '\n'.join(formatted_items) + f'\n... and {remaining_count} more items'
    else:
        display_items = [item.replace("File: ", "").replace("Directory: ", "") for item in copied_items]
        display_message = '\n'.join(f"<b>{os.path.basename(item)}</b>" for item in display_items)
    
    success_msg = f"Copied {len(copied_items)} items to stream:\n{display_message}"
    success_msg += f"\n{sync_status}"
    
    yd_menu.show_notification(success_msg, Constants.TIMEOUT_MEDIUM)


def _handle_batch_move_to_stream(yd_menu: YandexDiskMenu, processed_items: list) -> None:
    """Handle batch move to stream operation"""
    import errno
    moved_items = []
    errors = []
    
    for src_file_path, file_name, rename_back in processed_items:
        try:
            if os.path.isdir(src_file_path):
                base_name = os.path.basename(src_file_path.rstrip(os.sep))
                dest_dir = os.path.join(yd_menu.stream_dir, base_name)
                try:
                    shutil.move(src_file_path, dest_dir)
                    moved_items.append(f"Directory: {src_file_path}")
                except OSError as e:
                    if e.errno == errno.ENOTDIR:
                        shutil.move(src_file_path, dest_dir)
                        moved_items.append(f"File: {src_file_path}")
                    else:
                        raise
            else:
                shutil.move(src_file_path, yd_menu.stream_dir)
                moved_items.append(f"File: {src_file_path}")
            
            # No rename back for move operations since file is moved
            
        except Exception as e:
            errors.append((src_file_path, str(e)))
            yd_menu.logger.error(f"Error moving {src_file_path}: {e}")
    
    sync_status = yd_menu.sync_yandex_disk()
    
    # Handle errors but don't exit - show what succeeded and what failed
    if errors and moved_items:
        # Some succeeded, some failed
        error_details = '\n'.join(f"<b>{os.path.basename(fp)}</b>: {err}" for fp, err in errors[:3])
        if len(errors) > 3:
            error_details += f"\n... and {len(errors) - 3} more errors"
        yd_menu.show_notification(f"Moved {len(moved_items)} items, {len(errors)} failed:\n{error_details}", 
                                 Constants.TIMEOUT_MEDIUM, 'warn')
    elif errors:
        # All failed
        error_details = '\n'.join(f"<b>{os.path.basename(fp)}</b>: {err}" for fp, err in errors[:3])
        if len(errors) > 3:
            error_details += f"\n... and {len(errors) - 3} more errors"
        yd_menu.show_notification(f"Move failed for all items:\n{error_details}", Constants.TIMEOUT_ERROR, 'error')
        return
    
    # Create notification message showing first 5 items with count of remaining - format file names
    if len(moved_items) > 5:
        display_items = [item.replace("File: ", "").replace("Directory: ", "") for item in moved_items[:5]]
        formatted_items = [f"<b>{os.path.basename(item)}</b>" for item in display_items]
        remaining_count = len(moved_items) - 5
        display_message = '\n'.join(formatted_items) + f'\n... and {remaining_count} more items'
    else:
        display_items = [item.replace("File: ", "").replace("Directory: ", "") for item in moved_items]
        display_message = '\n'.join(f"<b>{os.path.basename(item)}</b>" for item in display_items)
    
    success_msg = f"Moved {len(moved_items)} items to stream:\n{display_message}"
    success_msg += f"\n{sync_status}"
    
    yd_menu.show_notification(success_msg, Constants.TIMEOUT_MEDIUM)


def _log_file_info(yd_menu: YandexDiskMenu, file_path: str, src_file_path: str, file_name: str, 
                   file_dir: str, is_outside_file: bool) -> None:
    """Log file information for debugging (DEBUG level only)"""
    yd_menu.logger.debug(f"File info - path: {file_path}")
    yd_menu.logger.debug(f"  - src_file_path: {src_file_path}")
    yd_menu.logger.debug(f"  - file_name: {file_name}")
    yd_menu.logger.debug(f"  - file_dir: {file_dir}")
    yd_menu.logger.debug(f"  - is_outside_file: {is_outside_file}")


import sys




def _handle_publish_command(yd_menu: YandexDiskMenu, command_type: str, src_file_path: str, 
                           is_outside_file: bool, ya_disk_file_path: str) -> None:
    """Handle publish commands, now supports directories as a whole (not recursively)"""
    use_com = command_type == 'PublishToYandexCom'
    yd_menu.publish_file(src_file_path, use_com)
    if os.path.isdir(src_file_path):
        yd_menu.show_notification(f"Published directory {src_file_path}", Constants.TIMEOUT_SHORT)
    else:
        yd_menu.show_notification(f"Published file {src_file_path}", Constants.TIMEOUT_SHORT)
    # For outside files or directories, move to stream directory after publishing
    if is_outside_file:
        shutil.move(ya_disk_file_path, yd_menu.stream_dir)


def _handle_clipboard_publish_command(yd_menu: YandexDiskMenu, command_type: str) -> None:
    """Handle clipboard publish commands"""
    clip_dest_path = yd_menu.get_clipboard_content()
    if not clip_dest_path:
        sys.exit(Constants.EXIT_CODE_ERROR)
        
    sync_status = yd_menu.sync_yandex_disk()
    yd_menu.show_notification(f"Clipboard flushed to stream:\n<b>{clip_dest_path}</b>\n{sync_status}", 
                             Constants.TIMEOUT_SHORT)
    
    use_com = command_type == 'ClipboardPublishToCom'
    yd_menu.wait_for_ready()
    yd_menu.publish_file(clip_dest_path, use_com)


def _handle_unpublish_command(yd_menu: YandexDiskMenu, src_file_path: str, file_name: str, is_outside_file: bool) -> None:
    """Handle unpublish command"""
    target_file = f"{yd_menu.stream_dir}/{file_name}" if is_outside_file else src_file_path
    result = yd_menu.unpublish_file(target_file)
    
    if any(error in result.lower() for error in ['unknown error', 'error:']):
        yd_menu.show_error_and_exit(f"{result} for <b>{file_name}</b>.", f"{result} - {file_name}")
    
    yd_menu.show_notification(f"{result} for <b>{file_name}</b>.", Constants.TIMEOUT_SHORT)


def _handle_unpublish_all_command(yd_menu: YandexDiskMenu, src_file_path: str, file_name: str, 
                                 file_dir: str, is_outside_file: bool) -> None:
    """Handle unpublish all copies command"""
    if is_outside_file:
        result = yd_menu.unpublish_copies(yd_menu.stream_dir, f"{yd_menu.stream_dir}/{file_name}", file_name)
    else:
        result = yd_menu.unpublish_copies(file_dir, src_file_path, file_name)
    
    timeout = Constants.TIMEOUT_ERROR if 'error' in result.lower() else Constants.TIMEOUT_MEDIUM
    icon_type = 'error' if 'error' in result.lower() else 'info'
    yd_menu.show_notification(f"Files unpublished:\n{result}", timeout, icon_type)


def _handle_clipboard_to_stream_command(yd_menu: YandexDiskMenu) -> None:
    """Handle clipboard to stream command"""
    clip_dest_path = yd_menu.get_clipboard_content()
    if not clip_dest_path:
        sys.exit(Constants.EXIT_CODE_ERROR)
        
    sync_status = yd_menu.sync_yandex_disk()
    yd_menu.show_notification(f"Clipboard flushed to stream:\n<b>{clip_dest_path}</b>\n{sync_status}", 
                             Constants.TIMEOUT_MEDIUM)


def _handle_file_add_to_stream_command(yd_menu: YandexDiskMenu, src_file_path: str) -> None:
    """Handle file or directory add to stream command"""
    import errno
    if os.path.isdir(src_file_path):
        base_name = os.path.basename(src_file_path.rstrip(os.sep))
        dest_dir = os.path.join(yd_menu.stream_dir, base_name)
        try:
            shutil.copytree(src_file_path, dest_dir)
            msg = f"Directory <b>{src_file_path}</b> copied to stream as {dest_dir}."
        except OSError as e:
            if e.errno == errno.ENOTDIR:
                shutil.copy2(src_file_path, dest_dir)
                msg = f"File <b>{src_file_path}</b> copied to stream."
            else:
                raise
    else:
        shutil.copy2(src_file_path, yd_menu.stream_dir)
        msg = f"File <b>{src_file_path}</b> copied to stream."
    sync_status = yd_menu.sync_yandex_disk()
    yd_menu.show_notification(f"{msg}\n{sync_status}", Constants.TIMEOUT_SHORT)


def _handle_file_move_to_stream_command(yd_menu: YandexDiskMenu, src_file_path: str) -> None:
    """Handle file or directory move to stream command"""
    import errno
    if os.path.isdir(src_file_path):
        base_name = os.path.basename(src_file_path.rstrip(os.sep))
        dest_dir = os.path.join(yd_menu.stream_dir, base_name)
        try:
            shutil.move(src_file_path, dest_dir)
            msg = f"Directory <b>{src_file_path}</b> moved to stream as {dest_dir}."
        except OSError as e:
            if e.errno == errno.ENOTDIR:
                shutil.move(src_file_path, dest_dir)
                msg = f"File <b>{src_file_path}</b> moved to stream."
            else:
                raise
    else:
        shutil.move(src_file_path, yd_menu.stream_dir)
        msg = f"File <b>{src_file_path}</b> moved to stream."
    sync_status = yd_menu.sync_yandex_disk()
    yd_menu.show_notification(f"{msg}\n{sync_status}", Constants.TIMEOUT_SHORT)




class CommandProcessor:
    """Handles command routing and processing logic for multiple files/directories"""
    
    def __init__(self, yd_menu: YandexDiskMenu):
        self.yd_menu = yd_menu
        # Use the logger from the YandexDiskMenu instance
        self.logger = yd_menu.logger
    
    def process_command(self, command_type: str, file_paths: tuple) -> None:
        """Main command processing logic with different algorithms"""
        self.logger.info(f"Processing command: {command_type} with {len(file_paths)} files")
        
        # Handle clipboard commands (no file processing needed)
        if command_type in Constants.CLIPBOARD_COMMANDS:
            self._execute_command(command_type, '', '', '', False, '')
            return

        # Handle all-at-once commands (batch processing)
        if command_type in Constants.ALL_AT_ONCE_COMMANDS:
            self._handle_batch_command(command_type, file_paths)
            return

        # Handle one-by-one commands (individual processing)
        if command_type in Constants.ONE_BY_ONE_COMMANDS:
            self._handle_individual_commands(command_type, file_paths)
            return

        # Handle unknown commands
        self._handle_unknown_command(command_type)
    
    def _execute_command(self, command_type: str, src_file_path: str, file_name: str, file_dir: str, 
                        is_outside_file: bool, ya_disk_file_path: str) -> None:
        """Execute the specified command type via handler switch statement"""
        if command_type in ('PublishToYandexCom', 'PublishToYandex'):
            _handle_publish_command(self.yd_menu, command_type, src_file_path, is_outside_file, ya_disk_file_path)
        elif command_type in ('ClipboardPublishToCom', 'ClipboardPublish'):
            _handle_clipboard_publish_command(self.yd_menu, command_type)
        elif command_type == 'UnpublishFromYandex':
            _handle_unpublish_command(self.yd_menu, src_file_path, file_name, is_outside_file)
        elif command_type == 'UnpublishAllCopy':
            _handle_unpublish_all_command(self.yd_menu, src_file_path, file_name, file_dir, is_outside_file)
        elif command_type == 'ClipboardToStream':
            _handle_clipboard_to_stream_command(self.yd_menu)
        elif command_type == 'FileAddToStream':
            _handle_file_add_to_stream_command(self.yd_menu, src_file_path)
        elif command_type == 'FileMoveToStream':
            _handle_file_move_to_stream_command(self.yd_menu, src_file_path)
        else:
            self._handle_unknown_command(command_type)
    
    def _handle_individual_commands(self, command_type: str, file_paths: tuple) -> None:
        """Handle commands that process items one by one (publish, save, remove/unpublish actions)"""
        self.logger.debug(f"Individual processing: {command_type}, {len(file_paths)} files")

        errors = []
        processed_count = 0
        collected_links = []  # For collecting publish links
        
        for file_path in file_paths:
            try:
                self.logger.debug(f"Processing: {file_path}")
                src_file_path, file_name, file_dir, is_outside_file = self.yd_menu._parse_file_info(file_path)
                
                # Log file information using helper method
                _log_file_info(self.yd_menu, file_path, src_file_path, file_name, file_dir, is_outside_file)
                
                original_src_file_path = src_file_path
                src_file_path, file_name, is_file_name_changed = self.yd_menu._rename_file_if_needed(
                    src_file_path, file_name, file_dir, is_outside_file, command_type)
                
                if is_file_name_changed:
                    self.logger.debug(f"Renamed: {original_src_file_path} -> {src_file_path}")
                
                rename_back = self.yd_menu._create_rename_back_function(
                    is_file_name_changed, src_file_path, original_src_file_path)
                ya_disk_file_path = f"{self.yd_menu.ya_disk}/{file_name}"
                
                # For publish commands, collect the link instead of copying immediately
                if command_type in ('PublishToYandexCom', 'PublishToYandex'):
                    link = _handle_publish_command_collect_link(self.yd_menu, command_type, src_file_path, is_outside_file, ya_disk_file_path)
                    if link:
                        collected_links.append(link)
                        self.logger.info(f"Published: {file_path}")
                else:
                    self._execute_command(command_type, src_file_path, file_name, file_dir, 
                                        is_outside_file, ya_disk_file_path)
                
                rename_back()
                processed_count += 1
                
            except Exception as e:
                errors.append((file_path, str(e)))
                self.logger.error(f"Error processing {file_path}: {e}")
        
        # Copy all collected links to clipboard at once
        if collected_links:
            all_links = '\n'.join(collected_links)
            self.yd_menu._copy_to_clipboard(all_links)
            
            # Format the notification to show links properly
            if len(collected_links) <= 3:
                # Show all links if 3 or fewer
                formatted_links = '\n'.join(self.yd_menu.format_link(link) for link in collected_links)
                message = f"Published {len(collected_links)} items. All links copied:\n{formatted_links}"
            else:
                # Show first 3 links with count
                formatted_links = '\n'.join(self.yd_menu.format_link(link) for link in collected_links[:3])
                message = f"Published {len(collected_links)} items. All links copied:\n{formatted_links}\n... and {len(collected_links) - 3} more links"
            
            self.yd_menu.show_notification(message, Constants.TIMEOUT_MEDIUM)
        
        # Show summary notification including errors if any
        if errors and processed_count > 0:
            error_summary = f"Processed {processed_count} of {len(file_paths)} items. {len(errors)} failed."
            self.yd_menu.show_notification(error_summary, Constants.TIMEOUT_MEDIUM, 'warn')
            # Show detailed errors in separate notification
            error_details = '\n'.join(f"<b>{os.path.basename(fp)}</b>: {err}" for fp, err in errors[:3])
            if len(errors) > 3:
                error_details += f"\n... and {len(errors) - 3} more errors"
            self.yd_menu.show_notification(f"Errors occurred:\n{error_details}", Constants.TIMEOUT_ERROR, 'error')
        elif errors:
            # All items failed
            error_details = '\n'.join(f"<b>{os.path.basename(fp)}</b>: {err}" for fp, err in errors[:3])
            if len(errors) > 3:
                error_details += f"\n... and {len(errors) - 3} more errors"
            self.yd_menu.show_notification(f"All items failed:\n{error_details}", Constants.TIMEOUT_ERROR, 'error')
        elif processed_count > 1 and not collected_links:
            self.yd_menu.show_notification(f"Processed {processed_count} items with {command_type}", self.Constants.TIMEOUT_SHORT)
        
        self.logger.info(f"Individual processing completed: {processed_count} processed, {len(collected_links)} links, {len(errors)} errors")

    def _handle_batch_command(self, command_type: str, file_paths: tuple) -> None:
        """Handle commands that process all items at once (file copy/move actions)"""
        self.logger.debug(f"Batch processing: {command_type}, {len(file_paths)} files")
        
        if not file_paths:
            self.yd_menu.show_notification("No files selected for batch operation", self.yd_menu.TIMEOUT_SHORT, 'warn')
            return
        
        errors = []
        processed_items = []
        is_copy_operation = command_type == 'FileAddToStream'
        
        # Process all files/directories with rename logic
        for file_path in file_paths:
            try:
                self.logger.debug(f"Processing: {file_path}")
                src_file_path, file_name, file_dir, is_outside_file = self.yd_menu._parse_file_info(file_path)
                
                # Log file information using helper method
                _log_file_info(self.yd_menu, file_path, src_file_path, file_name, file_dir, is_outside_file)
                
                original_src_file_path = src_file_path
                
                # Apply rename logic for both copy and move operations to avoid conflicts
                src_file_path, file_name, is_file_name_changed = self.yd_menu._rename_file_if_needed(
                    src_file_path, file_name, file_dir, is_outside_file, command_type)
                
                if is_file_name_changed:
                    self.logger.debug(f"Renamed: {original_src_file_path} -> {src_file_path}")
                
                if is_copy_operation:
                    # For copy operations, create rename back function
                    rename_back = self.yd_menu._create_rename_back_function(
                        is_file_name_changed, src_file_path, original_src_file_path)
                    processed_items.append((src_file_path, file_name, rename_back))
                else:
                    # For move operations, no rename back needed since file will be moved from original location
                    processed_items.append((src_file_path, file_name, lambda: None))
                    
            except Exception as e:
                errors.append((file_path, str(e)))
                self.logger.error(f"Error parsing {file_path}: {e}")
        
        if errors:
            error_details = '\n'.join(f"<b>{os.path.basename(fp)}</b>: {err}" for fp, err in errors[:3])
            if len(errors) > 3:
                error_details += f"\n... and {len(errors) - 3} more errors"
            self.yd_menu.show_notification(f"Batch processing errors:\n{error_details}", Constants.TIMEOUT_ERROR, 'error')
        
        # Execute batch operation
        if is_copy_operation:
            _handle_batch_add_to_stream(self.yd_menu, processed_items)
        elif command_type == 'FileMoveToStream':
            _handle_batch_move_to_stream(self.yd_menu, processed_items)
        else:
            self.yd_menu.show_notification(f"Unknown batch command: {command_type}", self.yd_menu.TIMEOUT_SHORT, 'error')
        
        self.logger.debug(f"Batch processing completed: {len(processed_items)} items")
    
    def _handle_unknown_command(self, command_type: str) -> None:
        """Handle unknown command"""
        work_path = f"{os.path.expanduser('~')}/{self.yd_menu.KDE_SERVICE_MENU_PATH}"
        self.yd_menu.show_notification(f"<b>Unknown action {command_type}</b>.\n\nCheck the menu files in <a href='file://{work_path}'>{work_path}</a> for available actions.", Constants.TIMEOUT_ERROR, 'error')
        self.logger.warning(f"Unknown action: {command_type}")

import click
@click.command()
@click.argument('command_type')
@click.argument('file_paths', nargs=-1, required=False)
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging (disabled by default)')
def main(command_type: str, file_paths: tuple = (), verbose: bool = False):
    main_impl(command_type, file_paths, verbose)

if __name__ == '__main__':
    main()
