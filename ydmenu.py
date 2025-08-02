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
                    signatures = YandexDiskMenu.IMAGE_SIGNATURES
                    if any(data.startswith(sig) for sig in signatures.values()):
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
    
    # Path constants
    ICON_BASE_PATH = '/usr/share/yd-tools/icons'
    ICONS = {
        'info': f'{ICON_BASE_PATH}/yd-128.png',
        'warn': f'{ICON_BASE_PATH}/yd-128_g.png',
        'error': f'{ICON_BASE_PATH}/light/yd-ind-error.png'
    }
    
    # Directory and file name constants
    YANDEX_DISK_DIR = 'yaMedia'
    STREAM_DIR = 'Media'
    LOG_FILE_NAME = 'yaMedia-python.log'
    NOTE_FILE_PREFIX = 'note-'
    KDE_SERVICE_MENU_PATH = '.local/share/kservices5/ServiceMenus'
    
    # File extension constants
    DEFAULT_IMAGE_EXT = 'png'
    DEFAULT_TEXT_EXT = 'txt'
    
    # URL constants
    YANDEX_DISK_URL_BASE = 'https://disk.yandex.com'
    YANDEX_SHORT_URL_MARKER = '.sk'
    
    # Image file signatures
    IMAGE_SIGNATURES = {
        'PNG': b'\x89PNG',
        'JPEG': b'\xff\xd8\xff',
        'BMP': b'BM',
        'GIF87a': b'GIF87a',
        'GIF89a': b'GIF89a'
    }
    
    # Application constants
    TITLE = 'Yandex.Disk'
    WAIT_TIMEOUT = 30
    
    # Timeout constants
    TIMEOUT_SHORT = 5
    TIMEOUT_MEDIUM = 10
    TIMEOUT_LONG = 30
    TIMEOUT_SYNC = 60
    TIMEOUT_ERROR = 15
    SLEEP_INTERVAL = 1

    # Numeric constants
    UUID_HEX_LENGTH = 8
    TEXT_SUMMARY_LENGTH = 30
    EXIT_CODE_ERROR = 1

    DEFAULT_INDEX = 0
    SPLIT_INDEX_LAST = -1
    FIRST_LINE_INDEX = 0
    INCREMENT_STEP = 1
    
    def __init__(self, verbose: bool = False):
        # Get environment variables
        self.ya_disk_root = os.environ.get('YA_DISK_ROOT', f"{os.path.expanduser('~')}/Public")
        self.ya_disk = f"{self.ya_disk_root}/{self.YANDEX_DISK_DIR}"
        self.stream_dir = f"{self.ya_disk}/{self.STREAM_DIR}"
        self.log_file_path = f"{self.ya_disk_root}/{self.LOG_FILE_NAME}"
        self.verbose = verbose
        
        self.start_time = time.time()
        
        # Setup logging with verbosity control
        # Use a unique logger name to avoid handler duplication across instances
        import uuid
        logger_name = f'YandexDiskMenu_{uuid.uuid4().hex[:self.UUID_HEX_LENGTH]}'
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
            
    def show_notification(self, message: str, timeout: int = None, icon_type: str = 'info') -> None:
        """Show KDE notification using kdialog"""
        if timeout is None:
            timeout = self.TIMEOUT_SHORT
        icon = self.ICONS.get(icon_type, self.ICONS['info'])
        elapsed_time = int(time.time() - self.start_time)
        full_message = f"{message}\nTime: {elapsed_time}s"
        
        try:
            subprocess.run([
                'kdialog', '--icon', icon, '--title', self.TITLE,
                '--passivepopup', full_message, str(timeout)
            ], check=False, timeout=self.TIMEOUT_MEDIUM)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            # Fallback to logging if kdialog not available or times out
            self.logger.warning(f"NOTIFICATION: {full_message}")
        
        self.logger.info(message)
    
    def show_error_and_exit(self, message: str, log_message: str = None) -> None:
        """Show error notification and exit"""
        error_msg = log_message or message
        self.logger.error(error_msg)
            
        notification_msg = f"{message}\nSee <a href='file://{self.log_file_path}'>log</a> for details"
        self.show_notification(notification_msg, self.TIMEOUT_ERROR, 'error')
        sys.exit(self.EXIT_CODE_ERROR)
    
    def _run_command(self, cmd: List[str], timeout: int = None, check: bool = True, input: str = None) -> subprocess.CompletedProcess:
        """Helper method to run subprocess commands with consistent error handling and logging"""
        timeout = timeout or self.TIMEOUT_LONG
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
            raise subprocess.CalledProcessError(self.EXIT_CODE_ERROR, cmd, f"Command timed out after {timeout}s")
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
        return status_line.split(':', self.SPLIT_INDEX_LAST)[self.SPLIT_INDEX_LAST].strip() if ':' in status_line else 'not started'
    
    def _get_yandex_status(self, timeout: int = None) -> str:
        """Get current yandex-disk status"""
        timeout = timeout or self.TIMEOUT_MEDIUM
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
        
        self.show_notification(f"<b>Service status: {status_code}</b>.\nWill wait for <b>{self.WAIT_TIMEOUT}s</b> and exit if no luck.", 
                             self.TIMEOUT_ERROR, 'warn')
        
        for i in range(self.WAIT_TIMEOUT):
            status_code = self._get_yandex_status(timeout=self.TIMEOUT_SHORT)
            if status_code == 'idle':
                self.logger.debug(f"Yandex-disk ready after {i+self.INCREMENT_STEP} seconds")
                return
            time.sleep(self.SLEEP_INTERVAL)
            
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
                                     timeout=self.TIMEOUT_SHORT, check=False)
            return next((line.strip() for line in result.stdout.split('\n') 
                        if line.strip().startswith('image')), None)
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.logger.debug("xclip not available or no image in clipboard")
            return None
    
    def _save_clipboard_image(self, target_type: str, current_date: str) -> str:
        """Save clipboard image to file using native Python libraries with xclip fallback"""
        extension = target_type.split('/')[self.SPLIT_INDEX_LAST] if '/' in target_type else self.DEFAULT_IMAGE_EXT
        full_path = f"{self.stream_dir}/{self.NOTE_FILE_PREFIX}{current_date}.{extension}"
        
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
            result = self._run_command(['xclip', '-selection', 'clipboard', '-o'], timeout=self.TIMEOUT_SHORT)
            self.logger.debug("Retrieved text content from clipboard using xclip fallback")
            return result.stdout
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.show_error_and_exit("Cannot access clipboard - all methods failed")
            return ""
    
    def _create_filename_from_text(self, content: str, current_date: str) -> str:
        """Create sanitized filename from text content"""
        name_summary = ''
        if content.strip():
            first_line = content.split('\n')[self.FIRST_LINE_INDEX][:self.TEXT_SUMMARY_LENGTH]
            # Remove problematic characters
            name_summary = re.sub(r'[<>|\\;/(),"\']|(https?:)|(:)|( {2})|( \.)+$', '', first_line).strip()
            if name_summary:
                name_summary = f" {name_summary}"
        
        return f"{self.stream_dir}/{self.NOTE_FILE_PREFIX}{current_date}{name_summary}.{self.DEFAULT_TEXT_EXT}"
    
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
                            timeout=self.TIMEOUT_SHORT, check=True, input=text)
            self.logger.debug(f"Copied to clipboard using xclip fallback: {text}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.show_error_and_exit("Cannot copy to clipboard - all methods failed")
    
    def _create_com_link(self, publish_path: str) -> str:
        """Convert .ru link to .com domain"""
        return f"{self.YANDEX_DISK_URL_BASE}{publish_path.split(self.YANDEX_SHORT_URL_MARKER, self.INCREMENT_STEP)[self.SPLIT_INDEX_LAST]}" if self.YANDEX_SHORT_URL_MARKER in publish_path else publish_path
    
    def _validate_publish_result(self, publish_path: str) -> None:
        """Validate yandex-disk publish result for errors"""
        error_indicators = ['unknown publish error', 'unknown error', 'error:']
        if any(error in publish_path.lower() for error in error_indicators):
            self.show_error_and_exit(f"<b>{publish_path}</b>", publish_path)
    
    def publish_file(self, file_path: str, use_com_domain: bool = True) -> None:
        """Publish file and copy link to clipboard"""
        try:
            result = self._run_command(['yandex-disk', 'publish', file_path], timeout=self.TIMEOUT_LONG)
            publish_path = result.stdout.strip()
            
            self._validate_publish_result(publish_path)
            com_link = self._create_com_link(publish_path)
            
            self.logger.info(file_path)
            self.logger.info(publish_path)
            self.logger.info(com_link)
            if use_com_domain:                
                self._copy_to_clipboard(com_link)
            else:
                self._copy_to_clipboard(publish_path)
            
            #message = (f"Public link to the {file_path} is copied to the clipboard.\n"
            #          f"<a href='{com_link}'><b>{com_link}</b></a>\n"
            #          f"<a href='{publish_path}'><b>{publish_path}</b></a>")
            #self.show_notification(message, self.TIMEOUT_ERROR)
            
        except subprocess.CalledProcessError as e:
            self.show_error_and_exit(f"Publish error: {e}")
    
    def unpublish_file(self, file_path: str) -> str:
        """Unpublish a single file"""
        try:
            result = self._run_command(['yandex-disk', 'unpublish', file_path], timeout=self.TIMEOUT_LONG)
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
        index = self.DEFAULT_INDEX
        
        while True:
            if index == self.DEFAULT_INDEX:
                current_file = base_file
                current_name = file_name
            else:
                current_name = f"{name_part}_{index}{ext_part}"
                current_file = f"{base_dir}/{current_name}"
            
            if not os.path.exists(current_file):
                break
                
            result = self.unpublish_file(current_file)
            results.append(f"<b>{current_name}</b> - {result}")
            
            index += self.INCREMENT_STEP
        
        return ';\n'.join(results)
    
    def sync_yandex_disk(self) -> str:
        """Trigger yandex-disk sync"""
        try:
            result = self._run_command(['yandex-disk', 'sync'], timeout=self.TIMEOUT_SYNC)
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
        
        index = self.DEFAULT_INDEX
        while True:
            if index == self.DEFAULT_INDEX:
                new_filename = filename
            else:
                new_filename = f"{name_part}_{index}{ext_part}"
            
            ya_disk_path = f"{self.ya_disk}/{new_filename}"
            stream_path = f"{self.stream_dir}/{new_filename}"
            target_path = f"{target_dir}/{new_filename}"
            
            if not any(os.path.exists(p) for p in [ya_disk_path, stream_path, target_path]):
                return new_filename
                
            index += self.INCREMENT_STEP
    
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
            
        stream_file_path = f"{self.stream_dir}/{file_name}"
        ya_disk_file_path = f"{self.ya_disk}/{file_name}"
        
        has_conflict = os.path.exists(stream_file_path) or os.path.exists(ya_disk_file_path)
        needs_rename = ((is_outside_file and command_type.startswith('PublishToYandex')) or 
                       command_type.startswith('File'))
        
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
        
        index = self.DEFAULT_INDEX
        while True:
            index += self.INCREMENT_STEP
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


def main_impl(command_type: str, file_paths: tuple = (), k_param: str = '', c_param: str = '', verbose: bool = False):
    """Yandex Disk menu actions for KDE Dolphin (now supports multiple files/dirs)"""
    yd_menu = YandexDiskMenu(verbose=verbose)
    yd_menu.log_message(f"Start - Command: {command_type}")
    yd_menu.wait_for_ready()

    if not file_paths:
        file_paths = ()

    errors = []
    for file_path in file_paths:
        try:
            src_file_path, file_name, file_dir, is_outside_file = yd_menu._parse_file_info(file_path)
            original_src_file_path = src_file_path
            src_file_path, file_name, is_file_name_changed = yd_menu._rename_file_if_needed(
                src_file_path, file_name, file_dir, is_outside_file, command_type)
            rename_back = yd_menu._create_rename_back_function(
                is_file_name_changed, src_file_path, original_src_file_path)
            ya_disk_file_path = f"{yd_menu.ya_disk}/{file_name}"
            _execute_command(yd_menu, command_type, src_file_path, file_name, file_dir, 
                            is_outside_file, ya_disk_file_path, c_param)
            #should_rename_back = not (is_outside_file and command_type.startswith('PublishToYandex'))
            rename_back()
        except Exception as e:
            errors.append((file_path, str(e)))
            yd_menu.logger.error(f"Error processing {file_path}: {e}")
    if errors:
        yd_menu.show_error_and_exit(f"Errors occurred:\n" + '\n'.join(f"{fp}: {err}" for fp, err in errors))
    yd_menu.log_message("Done")


import sys

def _execute_command(yd_menu: YandexDiskMenu, command_type: str, src_file_path: str, 
                    file_name: str, file_dir: str, is_outside_file: bool, 
                    ya_disk_file_path: str, c_param: str) -> None:
    """Execute the specified command type via handler switch statement"""
    if command_type in ('PublishToYandexCom', 'PublishToYandex'):
        _handle_publish_command(yd_menu, command_type, src_file_path, is_outside_file, ya_disk_file_path)
    elif command_type in ('ClipboardPublishToCom', 'ClipboardPublish'):
        _handle_clipboard_publish_command(yd_menu, command_type)
    elif command_type == 'UnpublishFromYandex':
        _handle_unpublish_command(yd_menu, src_file_path, file_name, is_outside_file)
    elif command_type == 'UnpublishAllCopy':
        _handle_unpublish_all_command(yd_menu, src_file_path, file_name, file_dir, is_outside_file)
    elif command_type == 'ClipboardToStream':
        _handle_clipboard_to_stream_command(yd_menu)
    elif command_type == 'FileAddToStream':
        _handle_file_add_to_stream_command(yd_menu, src_file_path)
    elif command_type == 'FileMoveToStream':
        _handle_file_move_to_stream_command(yd_menu, src_file_path)
    else:
        _handle_unknown_command(yd_menu, command_type, c_param)


def _handle_publish_command(yd_menu: YandexDiskMenu, command_type: str, src_file_path: str, 
                           is_outside_file: bool, ya_disk_file_path: str) -> None:
    """Handle publish commands, now supports directories as a whole (not recursively)"""
    use_com = command_type == 'PublishToYandexCom'
    yd_menu.publish_file(src_file_path, use_com)
    if os.path.isdir(src_file_path):
        yd_menu.show_notification(f"Published directory {src_file_path}", yd_menu.TIMEOUT_SHORT)
    else:
        yd_menu.show_notification(f"Published file {src_file_path}", yd_menu.TIMEOUT_SHORT)
    # For outside files or directories, move to stream directory after publishing
    if is_outside_file:
        shutil.move(ya_disk_file_path, yd_menu.stream_dir)


def _handle_clipboard_publish_command(yd_menu: YandexDiskMenu, command_type: str) -> None:
    """Handle clipboard publish commands"""
    clip_dest_path = yd_menu.get_clipboard_content()
    if not clip_dest_path:
        sys.exit(yd_menu.EXIT_CODE_ERROR)
        
    sync_status = yd_menu.sync_yandex_disk()
    yd_menu.show_notification(f"Clipboard flushed to stream:\n<b>{clip_dest_path}</b>\n{sync_status}", 
                             yd_menu.TIMEOUT_SHORT)
    
    use_com = command_type == 'ClipboardPublishToCom'
    yd_menu.wait_for_ready()
    yd_menu.publish_file(clip_dest_path, use_com)


def _handle_unpublish_command(yd_menu: YandexDiskMenu, src_file_path: str, file_name: str, is_outside_file: bool) -> None:
    """Handle unpublish command"""
    target_file = f"{yd_menu.stream_dir}/{file_name}" if is_outside_file else src_file_path
    result = yd_menu.unpublish_file(target_file)
    
    if any(error in result.lower() for error in ['unknown error', 'error:']):
        yd_menu.show_error_and_exit(f"{result} for <b>{file_name}</b>.", f"{result} - {file_name}")
    
    yd_menu.show_notification(f"{result} for <b>{file_name}</b>.", yd_menu.TIMEOUT_SHORT)


def _handle_unpublish_all_command(yd_menu: YandexDiskMenu, src_file_path: str, file_name: str, 
                                 file_dir: str, is_outside_file: bool) -> None:
    """Handle unpublish all copies command"""
    if is_outside_file:
        result = yd_menu.unpublish_copies(yd_menu.stream_dir, f"{yd_menu.stream_dir}/{file_name}", file_name)
    else:
        result = yd_menu.unpublish_copies(file_dir, src_file_path, file_name)
    
    timeout = yd_menu.TIMEOUT_ERROR if 'error' in result.lower() else yd_menu.TIMEOUT_MEDIUM
    icon_type = 'error' if 'error' in result.lower() else 'info'
    yd_menu.show_notification(f"Files unpublished:\n{result}", timeout, icon_type)


def _handle_clipboard_to_stream_command(yd_menu: YandexDiskMenu) -> None:
    """Handle clipboard to stream command"""
    clip_dest_path = yd_menu.get_clipboard_content()
    if not clip_dest_path:
        sys.exit(yd_menu.EXIT_CODE_ERROR)
        
    sync_status = yd_menu.sync_yandex_disk()
    yd_menu.show_notification(f"Clipboard flushed to stream:\n<b>{clip_dest_path}</b>\n{sync_status}", 
                             yd_menu.TIMEOUT_MEDIUM)


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
    yd_menu.show_notification(f"{msg}\n{sync_status}", yd_menu.TIMEOUT_SHORT)


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
    yd_menu.show_notification(f"{msg}\n{sync_status}", yd_menu.TIMEOUT_SHORT)


def _handle_unknown_command(yd_menu: YandexDiskMenu, command_type: str, c_param: str) -> None:
    """Handle unknown command"""
    work_path = f"{os.path.expanduser('~')}/{yd_menu.KDE_SERVICE_MENU_PATH}"
    yd_menu.show_notification(f"<b>Unknown action {command_type}</b>.\n\nCheck <a href='file://{work_path}/{c_param}'>{work_path}/{c_param}</a> for available actions.", yd_menu.TIMEOUT_ERROR)
    yd_menu.logger.warn(f"Unknown action: {command_type}")


import click
@click.command()
@click.argument('command_type')
@click.argument('file_paths', nargs=-1, required=False)
@click.argument('k_param', required=False)
@click.argument('c_param', required=False)
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging (disabled by default)')
def main(command_type: str, file_paths: tuple = (), k_param: str = '', c_param: str = '', verbose: bool = False):
    main_impl(command_type, file_paths, k_param, c_param, verbose)

if __name__ == '__main__':
    main()
