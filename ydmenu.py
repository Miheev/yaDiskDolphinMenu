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


class YandexDiskMenu:
    """Main class for Yandex Disk menu operations"""
    
    # Constants
    ICONS = {
        'info': '/usr/share/yd-tools/icons/yd-128.png',
        'warn': '/usr/share/yd-tools/icons/yd-128_g.png',
        'error': '/usr/share/yd-tools/icons/light/yd-ind-error.png'
    }
    TITLE = 'Yandex.Disk'
    WAIT_TIMEOUT = 30
    
    def __init__(self):
        # Get environment variables
        self.ya_disk_root = os.environ.get('YA_DISK_ROOT', f"{os.path.expanduser('~')}/Public")
        self.ya_disk = f"{self.ya_disk_root}/yaMedia"
        self.stream_dir = f"{self.ya_disk}/Media"
        self.log_file_path = f"{self.ya_disk_root}/yaMedia.log"
        
        self.start_time = time.time()
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file_path),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
    def log_message(self, message: str) -> None:
        """Log message using logging module"""
        logging.info(message)
            
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
            logging.warning(f"NOTIFICATION: {full_message}")
        
        logging.info(message)
    
    def show_error_and_exit(self, message: str, log_message: str = None) -> None:
        """Show error notification and exit"""
        error_msg = log_message or message
        logging.error(error_msg)
            
        notification_msg = f"{message}\nSee <a href='file://{self.log_file_path}'>log</a> for details"
        self.show_notification(notification_msg, 15, 'error')
        sys.exit(1)
    
    def _run_command(self, cmd: List[str], timeout: int = 30, check: bool = True) -> subprocess.CompletedProcess:
        """Helper method to run subprocess commands with consistent error handling"""
        try:
            return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=check)
        except subprocess.TimeoutExpired:
            raise subprocess.CalledProcessError(1, cmd, f"Command timed out after {timeout}s")
        except subprocess.CalledProcessError as e:
            logging.error(f"Command failed: {' '.join(cmd)}, Error: {e}")
            raise
    
    def wait_for_ready(self) -> None:
        """Wait for yandex-disk daemon to be ready"""
        try:
            result = subprocess.run(['yandex-disk', 'status'], 
                                  capture_output=True, text=True, timeout=10)
            status_line = next((line for line in result.stdout.split('\n') 
                              if line.strip().startswith('status')), '')
            status_code = status_line.split(':', 1)[1].strip() if ':' in status_line else 'not started'
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            status_code = 'not started'
        
        if status_code == 'idle':
            return
            
        self.show_notification(f"<b>Service status: {status_code}</b>.\nWill wait for <b>30s</b> and exit if no luck.", 
                             15, 'warn')
        
        wait_count = 30
        for i in range(wait_count):
            try:
                result = subprocess.run(['yandex-disk', 'status'], 
                                      capture_output=True, text=True, timeout=5)
                status_line = next((line for line in result.stdout.split('\n') 
                                  if line.strip().startswith('status')), '')
                status_code = status_line.split(':', 1)[1].strip() if ':' in status_line else 'not started'
                
                if status_code == 'idle':
                    return
                    
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
                pass
                
            time.sleep(1)
            
        self.show_error_and_exit(
            "<b>Service is not available</b>.\nTry later or restart it via\n<b><i>yandex-disk stop && yandex-disk start</i></b>.",
            "Service is not available"
        )
    
    def get_clipboard_content(self) -> Optional[str]:
        """Get clipboard content using xclip"""
        try:
            # Check if clipboard contains image
            result = subprocess.run(['xclip', '-selection', 'clipboard', '-t', 'TARGETS', '-o'],
                                  capture_output=True, text=True)
            target_type = next((line.strip() for line in result.stdout.split('\n') 
                              if line.strip().startswith('image')), None)
            
            current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            full_path = f'note-{current_date}'
            
            if target_type:
                # Image content
                extension = target_type.split('/')[-1] if '/' in target_type else 'png'
                full_path = f"{self.stream_dir}/note-{current_date}.{extension}"
                
                with open(full_path, 'wb') as f:
                    subprocess.run(['xclip', '-selection', 'clipboard', '-t', target_type, '-o'],
                                 stdout=f, check=True)
            else:
                # Text content
                result = subprocess.run(['xclip', '-selection', 'clipboard', '-o'],
                                      capture_output=True, text=True)
                content = result.stdout
                
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
            
            return full_path
            
        except (subprocess.CalledProcessError, IOError) as e:
            self.show_error_and_exit(f"Save clipboard error: {e}")
    
    def publish_file(self, file_path: str, use_com_domain: bool = True) -> None:
        """Publish file and copy link to clipboard"""
        try:
            result = subprocess.run(['yandex-disk', 'publish', file_path],
                                  capture_output=True, text=True, check=True)
            publish_path = result.stdout.strip()
            
            if any(error in publish_path.lower() for error in ['unknown publish error', 'unknown error', 'error:']):
                self.show_error_and_exit(f"<b>{publish_path}</b>", publish_path)
            
            # Create .com version of link
            com_link = f"https://disk.yandex.com{publish_path.split('.sk', 1)[-1]}" if '.sk' in publish_path else publish_path
            
            print(file_path)
            if use_com_domain:
                print(publish_path)
                # Copy .com link to clipboard
                subprocess.run(['xclip', '-selection', 'clipboard'], 
                             input=com_link, text=True)
            else:
                # Copy .ru link to clipboard
                subprocess.run(['xclip', '-selection', 'clipboard'], 
                             input=publish_path, text=True)
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
            result = subprocess.run(['yandex-disk', 'unpublish', file_path],
                                  capture_output=True, text=True, check=True)
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
            result = subprocess.run(['yandex-disk', 'sync'],
                                  capture_output=True, text=True, check=True)
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


@click.command()
@click.argument('command_type')
@click.argument('file_path', required=False)
@click.argument('k_param', required=False) 
@click.argument('c_param', required=False)
def main(command_type: str, file_path: str = '', k_param: str = '', c_param: str = ''):
    """Yandex Disk menu actions for KDE Dolphin"""
    
    yd_menu = YandexDiskMenu()
    yd_menu.log_message(f"Start - Command: {command_type}")
    
    # Parse file info
    src_file_path = file_path or ''
    file_name = os.path.basename(file_path) if file_path else ''
    file_dir = os.path.dirname(file_path) if file_path else ''
    
    # Check if file is outside ya_disk directory
    is_outside_file = not src_file_path.startswith(f"{yd_menu.ya_disk}/") if src_file_path else True
    
    yd_menu.wait_for_ready()
    
    # Handle file renaming for conflicts
    if file_path and os.path.exists(file_path):
        if ((os.path.exists(f"{yd_menu.stream_dir}/{file_name}") or 
             os.path.exists(f"{yd_menu.ya_disk}/{file_name}")) and
            (is_outside_file and command_type.startswith('PublishToYandex')) or 
            command_type.startswith('File')):
            
            new_filename = yd_menu.generate_unique_filename(file_dir, file_name)
            new_src_path = f"{file_dir}/{new_filename}"
            shutil.move(src_file_path, new_src_path)
            src_file_path = new_src_path
            file_name = new_filename
    
    # Handle different command types
    try:
        if command_type in ['PublishToYandexCom', 'PublishToYandex']:
            use_com = command_type == 'PublishToYandexCom'
            yd_menu.publish_file(src_file_path, use_com)
            
            if is_outside_file:
                shutil.move(src_file_path, yd_menu.stream_dir)
                
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
            
        else:
            work_path = f"{os.path.expanduser('~')}/.local/share/kservices5/ServiceMenus"
            yd_menu.show_notification(f"<b>Unknown action {command_type}</b>.\n\nCheck <a href='file://{work_path}/{c_param}'>{work_path}/{c_param}</a> for available actions.", 15)
            print(f"Unknown action: {command_type}")
            
    except Exception as e:
        yd_menu.show_error_and_exit(f"Unexpected error: {e}")
        
    yd_menu.log_message("Done")


if __name__ == '__main__':
    main()