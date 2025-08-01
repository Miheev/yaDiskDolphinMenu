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

import click
import pyperclip


class YandexDiskMenu:
    """Main class for Yandex Disk menu operations"""
    
    # Constants
    VERSION = '1.0-RC-1'
    ICONS = {
        'info': '/usr/share/yd-tools/icons/yd-128.png',
        'warn': '/usr/share/yd-tools/icons/yd-128_g.png',
        'error': '/usr/share/yd-tools/icons/light/yd-ind-error.png'
    }
    TITLE = 'Yandex.Disk'
    WAIT_TIMEOUT = 30
    
    def __init__(self, verbose: bool = False):
        # Get environment variables
        self.ya_disk_root = os.environ.get('YA_DISK_ROOT', f"{os.path.expanduser('~')}/Public")
        self.ya_disk = f"{self.ya_disk_root}/yaMedia"
        self.stream_dir = f"{self.ya_disk}/Media"
        self.log_file_path = f"{self.ya_disk_root}/yaMedia-python.log"
        self.verbose = verbose
        
        self.start_time = time.time()
        
        # Setup logging with verbosity control
        # Use a unique logger name to avoid handler duplication across instances
        import uuid
        logger_name = f'YandexDiskMenu_{uuid.uuid4().hex[:8]}'
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
            
    def show_notification(self, message: str, timeout: int = 5, icon_type: str = 'info') -> None:
        """Show KDE notification using kdialog"""
        icon = self.ICONS.get(icon_type, self.ICONS['info'])
        elapsed_time = int(time.time() - self.start_time)
        full_message = f"{message}\nTime: {elapsed_time}s"
        
        try:
            subprocess.run([
                'kdialog', '--icon', icon, '--title', self.TITLE,
                '--passivepopup', full_message, str(timeout)
            ], check=False, timeout=10)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            # Fallback to logging if kdialog not available or times out
            self.logger.warning(f"NOTIFICATION: {full_message}")
        
        self.logger.info(message)
    
    def show_error_and_exit(self, message: str, log_message: str = None) -> None:
        """Show error notification and exit"""
        error_msg = log_message or message
        self.logger.error(error_msg)
            
        notification_msg = f"{message}\nSee <a href='file://{self.log_file_path}'>log</a> for details"
        self.show_notification(notification_msg, 15, 'error')
        sys.exit(1)
    
    def _run_command(self, cmd: List[str], timeout: int = 30, check: bool = True, input: str = None) -> subprocess.CompletedProcess:
        """Helper method to run subprocess commands with consistent error handling and logging"""
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
            raise subprocess.CalledProcessError(1, cmd, f"Command timed out after {timeout}s")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Command failed: {' '.join(cmd)}, Return code: {e.returncode}")
            if e.stdout:
                self.logger.error(f"Command stdout: {e.stdout.strip()}")
            if e.stderr:
                self.logger.error(f"Command stderr: {e.stderr.strip()}")
            raise
    
    def wait_for_ready(self) -> None:
        """Wait for yandex-disk daemon to be ready"""
        try:
            result = self._run_command(['yandex-disk', 'status'], timeout=10, check=False)
            # Look for "Synchronization core status: idle" format
            status_line = next((line for line in result.stdout.split('\n') 
                              if 'status:' in line.lower()), '')
            status_code = status_line.split(':', -1)[-1].strip() if ':' in status_line else 'not started'
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            status_code = 'not started'
            self.logger.warning("Failed to get yandex-disk status")
        
        if status_code == 'idle':
            return
        
        self.show_notification(f"<b>Service status: {status_code}</b>.\nWill wait for <b>30s</b> and exit if no luck.", 
                             15, 'warn')
        
        wait_count = 30
        for i in range(wait_count):
            try:
                result = self._run_command(['yandex-disk', 'status'], timeout=5, check=False)
                # Look for "Synchronization core status: idle" format
                status_line = next((line for line in result.stdout.split('\n') 
                                  if 'status:' in line.lower()), '')
                status_code = status_line.split(':', -1)[-1].strip() if ':' in status_line else 'not started'
                
                if status_code == 'idle':
                    self.logger.debug(f"Yandex-disk ready after {i+1} seconds")
                    return
                    
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
                self.logger.debug(f"Status check attempt {i+1} failed")
                
            time.sleep(1)
            
        self.show_error_and_exit(
            "<b>Service is not available</b>.\nTry later or restart it via\n<b><i>yandex-disk stop && yandex-disk start</i></b>.",
            "Service is not available"
        )
    
    def get_clipboard_content(self) -> Optional[str]:
        """Get clipboard content using pyperclip and xclip fallback for images"""
        try:
            current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Check if clipboard contains image using xclip (pyperclip doesn't support images)
            try:
                result = self._run_command(['xclip', '-selection', 'clipboard', '-t', 'TARGETS', '-o'], 
                                         timeout=5, check=False)
                target_type = next((line.strip() for line in result.stdout.split('\n') 
                                  if line.strip().startswith('image')), None)
                
                if target_type:
                    # Image content - still use xclip for binary data
                    self.logger.debug(f"Clipboard contains image: {target_type}")
                    extension = target_type.split('/')[-1] if '/' in target_type else 'png'
                    full_path = f"{self.stream_dir}/note-{current_date}.{extension}"
                    
                    with open(full_path, 'wb') as f:
                        # For binary data, we need to use subprocess directly
                        subprocess.run(['xclip', '-selection', 'clipboard', '-t', target_type, '-o'],
                                      stdout=f, check=True)
                    
                    self.logger.info(f"Saved clipboard image to: {full_path}")
                    return full_path
                    
            except (subprocess.CalledProcessError, FileNotFoundError):
                self.logger.debug("xclip not available or no image in clipboard, trying text")
            
            # Text content using pyperclip
            try:
                content = pyperclip.paste()
                self.logger.debug("Retrieved text content from clipboard using pyperclip")
            except Exception as e:
                self.logger.warning(f"pyperclip failed, falling back to xclip: {e}")
                # Fallback to xclip for text
                try:
                    result = self._run_command(['xclip', '-selection', 'clipboard', '-o'], timeout=5)
                    content = result.stdout
                    self.logger.debug("Retrieved text content from clipboard using xclip")
                except (subprocess.CalledProcessError, FileNotFoundError):
                    self.show_error_and_exit("Cannot access clipboard - both pyperclip and xclip failed")
                    return None
            
            if not content or not content.strip():
                self.logger.warning("Clipboard is empty or contains only whitespace")
                return None
            
            # Create filename from first line, sanitized
            name_summary = ''
            if content.strip():
                first_line = content.split('\n')[0][:30]
                # Remove problematic characters
                name_summary = re.sub(r'[<>|\\;/(),"\']|(https?:)|(:)|( {2})|( \.)+$', '', first_line).strip()
                if name_summary:
                    name_summary = f" {name_summary}"
            
            full_path = f"{self.stream_dir}/note-{current_date}{name_summary}.txt"
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.logger.info(f"Saved clipboard text to: {full_path}")
            return full_path
            
        except (IOError, OSError) as e:
            self.show_error_and_exit(f"Save clipboard error: {e}")
    
    def publish_file(self, file_path: str, use_com_domain: bool = True) -> None:
        """Publish file and copy link to clipboard"""
        try:
            result = self._run_command(['yandex-disk', 'publish', file_path], timeout=30)
            publish_path = result.stdout.strip()
            
            if any(error in publish_path.lower() for error in ['unknown publish error', 'unknown error', 'error:']):
                self.show_error_and_exit(f"<b>{publish_path}</b>", publish_path)
            
            # Create .com version of link
            com_link = f"https://disk.yandex.com{publish_path.split('.sk', 1)[-1]}" if '.sk' in publish_path else publish_path
            
            print(file_path)
            if use_com_domain:
                print(publish_path)
                # Copy .com link to clipboard
                try:
                    pyperclip.copy(com_link)
                    self.logger.debug(f"Copied .com link to clipboard using pyperclip: {com_link}")
                except Exception as e:
                    self.logger.warning(f"pyperclip failed, falling back to xclip: {e}")
                    self._run_command(['xclip', '-selection', 'clipboard'], 
                                    timeout=5, check=True, input=com_link)
            else:
                # Copy .ru link to clipboard
                try:
                    pyperclip.copy(publish_path)
                    self.logger.debug(f"Copied .ru link to clipboard using pyperclip: {publish_path}")
                except Exception as e:
                    self.logger.warning(f"pyperclip failed, falling back to xclip: {e}")
                    self._run_command(['xclip', '-selection', 'clipboard'], 
                                    timeout=5, check=True, input=publish_path)
                print(com_link)
            
            message = (f"Public link to the {file_path} is copied to the clipboard.\n"
                      f"<a href='{com_link}'><b>{com_link}</b></a>\n"
                      f"<a href='{publish_path}'><b>{publish_path}</b></a>")
            self.show_notification(message, 15)
            
        except subprocess.CalledProcessError as e:
            self.show_error_and_exit(f"Publish error: {e}")
    
    def unpublish_file(self, file_path: str) -> str:
        """Unpublish a single file"""
        try:
            result = self._run_command(['yandex-disk', 'unpublish', file_path], timeout=30)
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
        index = 0
        
        while True:
            if index == 0:
                current_file = base_file
                current_name = file_name
            else:
                current_name = f"{name_part}_{index}{ext_part}"
                current_file = f"{base_dir}/{current_name}"
            
            if not os.path.exists(current_file):
                break
                
            result = self.unpublish_file(current_file)
            results.append(f"<b>{current_name}</b> - {result}")
            
            index += 1
        
        return ';\n'.join(results)
    
    def sync_yandex_disk(self) -> str:
        """Trigger yandex-disk sync"""
        try:
            result = self._run_command(['yandex-disk', 'sync'], timeout=60)
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
        
        index = 0
        while True:
            if index == 0:
                new_filename = filename
            else:
                new_filename = f"{name_part}_{index}{ext_part}"
            
            ya_disk_path = f"{self.ya_disk}/{new_filename}"
            stream_path = f"{self.stream_dir}/{new_filename}"
            target_path = f"{target_dir}/{new_filename}"
            
            if not any(os.path.exists(p) for p in [ya_disk_path, stream_path, target_path]):
                return new_filename
                
            index += 1
    
    def show_version(self) -> None:
        """Display version information"""
        message = f"<b>Yandex Disk Menu - Python Version {self.VERSION}</b><br/>\nKDE Dolphin integration for Yandex Disk sharing"
        self.show_notification(message, 10, 'info')
        self.logger.info(f"Version {self.VERSION} displayed")


@click.command()
@click.argument('command_type')
@click.argument('file_path', required=False)
@click.argument('k_param', required=False) 
@click.argument('c_param', required=False)
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging (disabled by default)')
def main(command_type: str, file_path: str = '', k_param: str = '', c_param: str = '', verbose: bool = False):
    """Yandex Disk menu actions for KDE Dolphin"""
    
    # SET TO True FOR DEBUG
    yd_menu = YandexDiskMenu(verbose=verbose)
    yd_menu.log_message(f"Start - Command: {command_type}")
    
    # Parse file info
    src_file_path = file_path or ''
    file_name = os.path.basename(file_path) if file_path else ''
    file_dir = os.path.dirname(file_path) if file_path else ''
    
    # Check if file is outside ya_disk directory
    is_outside_file = not src_file_path.startswith(f"{yd_menu.ya_disk}/") if src_file_path else True
    
    yd_menu.wait_for_ready()
    
    # Rename file if already exists in destination directories (following bash logic)
    is_file_name_changed = False
    original_src_file_path = src_file_path
    
    if file_path and os.path.exists(file_path):
        # Check for conflicts that require renaming (same logic as bash)
        stream_file_path = f"{yd_menu.stream_dir}/{file_name}"
        ya_disk_file_path = f"{yd_menu.ya_disk}/{file_name}"
        
        if ((os.path.exists(stream_file_path) or os.path.exists(ya_disk_file_path)) and
            ((is_outside_file and command_type.startswith('PublishToYandex')) or 
             command_type.startswith('File'))):
            
            # Generate unique filename using same logic as bash
            file_path_obj = Path(file_path)
            if file_name.startswith('.'):
                # Hidden file
                file_name_part = file_name
                ext_part = ''
            else:
                # Regular file
                file_name_part = file_path_obj.stem
                ext_part = file_path_obj.suffix
            
            index = 0
            while True:
                index += 1
                new_file_name = f"{file_name_part}_{index}{ext_part}"
                new_stream_path = f"{yd_menu.stream_dir}/{new_file_name}"
                new_ya_disk_path = f"{yd_menu.ya_disk}/{new_file_name}"
                new_src_path = f"{file_dir}/{new_file_name}"
                
                if (not os.path.exists(new_stream_path) and 
                    not os.path.exists(new_ya_disk_path) and 
                    not os.path.exists(new_src_path)):
                    break
            
            # Rename source file to the new unique name
            new_src_file_path = f"{file_dir}/{new_file_name}"
            yd_menu.logger.info(f"Renaming source file: {src_file_path} -> {new_src_file_path}")
            shutil.move(src_file_path, new_src_file_path)
            
            # Update variables
            src_file_path = new_src_file_path
            file_name = new_file_name
            ya_disk_file_path = new_ya_disk_path
            is_file_name_changed = True
    
    def rename_back():
        """Rename source file back to original name if it was changed"""
        if is_file_name_changed and os.path.exists(src_file_path):
            yd_menu.logger.info(f"Renaming back: {src_file_path} -> {original_src_file_path}")
            shutil.move(src_file_path, original_src_file_path)
    
    # Handle different command types
    try:
        if command_type in ['PublishToYandexCom', 'PublishToYandex']:
            use_com = command_type == 'PublishToYandexCom'
            yd_menu.publish_file(src_file_path, use_com)
            
            # For outside files, move to stream directory after publishing
            # Note: yandex-disk publish copies the file to the yandex disk directory first, 
            # that's why it need to be moved to the stream directory
            if is_outside_file:
                shutil.move(ya_disk_file_path, yd_menu.stream_dir)
                
        elif command_type in ['ClipboardPublishToCom', 'ClipboardPublish']:
            clip_dest_path = yd_menu.get_clipboard_content()
            if not clip_dest_path:
                sys.exit(1)
                
            sync_status = yd_menu.sync_yandex_disk()
            yd_menu.show_notification(f"Clipboard flushed to stream:\n<b>{clip_dest_path}</b>\n{sync_status}", 5)
            
            use_com = command_type == 'ClipboardPublishToCom'
            yd_menu.wait_for_ready()
            yd_menu.publish_file(clip_dest_path, use_com)
            
        elif command_type == 'UnpublishFromYandex':
            target_file = f"{yd_menu.stream_dir}/{file_name}" if is_outside_file else src_file_path
            result = yd_menu.unpublish_file(target_file)
            
            if any(error in result.lower() for error in ['unknown error', 'error:']):
                yd_menu.show_error_and_exit(f"{result} for <b>{file_name}</b>.", f"{result} - {file_name}")
            
            yd_menu.show_notification(f"{result} for <b>{file_name}</b>.", 5)
            
        elif command_type == 'UnpublishAllCopy':
            if is_outside_file:
                result = yd_menu.unpublish_copies(yd_menu.stream_dir, f"{yd_menu.stream_dir}/{file_name}", file_name)
            else:
                result = yd_menu.unpublish_copies(file_dir, src_file_path, file_name)
            
            timeout = 15 if 'error' in result.lower() else 10
            icon_type = 'error' if 'error' in result.lower() else 'info'
            yd_menu.show_notification(f"Files unpublished:\n{result}", timeout, icon_type)
            
        elif command_type == 'ClipboardToStream':
            clip_dest_path = yd_menu.get_clipboard_content()
            if not clip_dest_path:
                sys.exit(1)
                
            sync_status = yd_menu.sync_yandex_disk()
            yd_menu.show_notification(f"Clipboard flushed to stream:\n<b>{clip_dest_path}</b>\n{sync_status}", 10)
            
        elif command_type == 'FileAddToStream':
            shutil.copy2(src_file_path, yd_menu.stream_dir)
            sync_status = yd_menu.sync_yandex_disk()
            yd_menu.show_notification(f"<b>{src_file_path}</b> is copied to the file stream.\n{sync_status}", 5)
            
        elif command_type == 'FileMoveToStream':
            shutil.move(src_file_path, yd_menu.stream_dir)
            sync_status = yd_menu.sync_yandex_disk()
            yd_menu.show_notification(f"<b>{src_file_path}</b> is moved to the file stream.\n{sync_status}", 5)
            
        elif command_type == 'ShowVersion':
            yd_menu.show_version()
            
        else:
            work_path = f"{os.path.expanduser('~')}/.local/share/kservices5/ServiceMenus"
            yd_menu.show_notification(f"<b>Unknown action {command_type}</b>.\n\nCheck <a href='file://{work_path}/{c_param}'>{work_path}/{c_param}</a> for available actions.", 15)
            print(f"Unknown action: {command_type}")
            
    except Exception as e:
        # Ensure rename back happens even on error
        try:
            rename_back()
        except Exception as rollback_error:
            yd_menu.logger.error(f"Failed to rename back: {rollback_error}")
        
        yd_menu.show_error_and_exit(f"Unexpected error: {e}")
        
    # Rename back to original name (matches bash renameBack at end)
    rename_back()
    yd_menu.log_message("Done")


if __name__ == '__main__':
    main()
