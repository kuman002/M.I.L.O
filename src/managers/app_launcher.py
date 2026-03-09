"""
Application & File Launcher Module for MILO
Handles opening applications and files
"""

import os
import subprocess
import sys
import winreg
from typing import Dict, Optional, List
from pathlib import Path


class AppLauncher:
    """Handles opening applications and files"""
    
    def __init__(self):
        """Initialize app launcher with common applications"""
        self.common_apps = self._load_common_apps()
        self.file_handlers = self._load_file_handlers()
    
    def _load_common_apps(self) -> Dict[str, str]:
        """Load common application paths based on OS"""
        apps = {}
        
        if sys.platform == 'win32':
            # Start with hardcoded common apps
            apps.update({
                'notepad': 'notepad.exe',
                'calculator': 'calc.exe',
                'paint': 'mspaint.exe',
                'word': 'WINWORD.EXE',
                'excel': 'EXCEL.EXE',
                'powerpoint': 'POWERPNT.EXE',
                'chrome': 'chrome.exe',
                'firefox': 'firefox.exe',
                'edge': 'msedge.exe',
                'brave': 'brave.exe',
                'opera': 'opera.exe',
                'vscode': 'code.exe',
                'code': 'code.exe',
                'visual studio': 'devenv.exe',
                'file explorer': 'explorer.exe',
                'cmd': 'cmd.exe',
                'powershell': 'powershell.exe',
                'snipping tool': 'SnippingTool.exe',
                'settings': 'ms-settings:',
                'task manager': 'taskmgr.exe',
            })
            
            # Add dynamically discovered apps
            apps.update(self._discover_windows_apps())
            
        elif sys.platform == 'darwin':  # macOS
            apps.update({
                'notepad': 'TextEdit',
                'calculator': 'Calculator',
                'word': 'Microsoft Word',
                'excel': 'Microsoft Excel',
                'chrome': 'Google Chrome',
                'firefox': 'Firefox',
                'vscode': 'Visual Studio Code',
                'finder': 'Finder',
                'terminal': 'Terminal',
                'safari': 'Safari',
            })
        else:  # Linux
            apps.update({
                'notepad': 'gedit',
                'calculator': 'gnome-calculator',
                'chrome': 'google-chrome',
                'firefox': 'firefox',
                'vscode': 'code',
                'terminal': 'gnome-terminal',
                'file manager': 'nautilus',
            })
        
        return apps
    
    def _discover_windows_apps(self) -> Dict[str, str]:
        """Discover installed applications on Windows"""
        discovered_apps = {}
        
        try:
            # Scan Start Menu directories for .lnk files
            start_menu_paths = [
                Path.home() / 'AppData/Roaming/Microsoft/Windows/Start Menu/Programs',
                Path('C:/ProgramData/Microsoft/Windows/Start Menu/Programs')
            ]
            
            for start_menu_path in start_menu_paths:
                if start_menu_path.exists():
                    discovered_apps.update(self._scan_start_menu(start_menu_path))
            
            # Query Windows registry for installed applications
            discovered_apps.update(self._query_registry_apps())
            
            # Scan Program Files directories for executables
            discovered_apps.update(self._scan_program_files())
            
        except Exception as e:
            print(f"Warning: Failed to discover some Windows apps: {e}")
        
        return discovered_apps
    
    def _scan_start_menu(self, start_menu_path: Path) -> Dict[str, str]:
        """Scan Start Menu for application shortcuts"""
        apps = {}
        
        try:
            for lnk_file in start_menu_path.rglob('*.lnk'):
                try:
                    app_name = lnk_file.stem.lower()
                    # Skip duplicates and common system entries
                    if app_name not in apps and not any(skip in app_name for skip in ['uninstall', 'help', 'readme', 'update']):
                        apps[app_name] = str(lnk_file)
                except Exception:
                    continue
        except Exception:
            pass
        
        return apps
    
    def _query_registry_apps(self) -> Dict[str, str]:
        """Query Windows registry for installed applications"""
        apps = {}
        
        try:
            # Query Uninstall registry key for installed apps
            registry_paths = [
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
                r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
            ]
            
            for reg_path in registry_paths:
                try:
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path)
                    i = 0
                    while True:
                        try:
                            subkey = winreg.EnumKey(key, i)
                            subkey_handle = winreg.OpenKey(key, subkey)
                            
                            try:
                                display_name = winreg.QueryValueEx(subkey_handle, "DisplayName")[0]
                                install_location = winreg.QueryValueEx(subkey_handle, "InstallLocation")[0] if "InstallLocation" in [winreg.EnumValue(subkey_handle, j)[0] for j in range(winreg.QueryInfoKey(subkey_handle)[1])] else None
                                
                                if display_name and install_location:
                                    app_name = display_name.lower().strip()
                                    if app_name not in apps:
                                        # Look for main executable in install location
                                        exe_path = self._find_main_exe(install_location)
                                        if exe_path:
                                            apps[app_name] = exe_path
                                            
                            except FileNotFoundError:
                                pass
                            finally:
                                winreg.CloseKey(subkey_handle)
                                
                            i += 1
                        except OSError:
                            break
                            
                except FileNotFoundError:
                    continue
                finally:
                    try:
                        winreg.CloseKey(key)
                    except:
                        pass
                        
        except Exception:
            pass
        
        return apps
    
    def _scan_program_files(self) -> Dict[str, str]:
        """Scan Program Files directories for executables"""
        apps = {}
        
        try:
            program_dirs = [
                'C:/Program Files',
                'C:/Program Files (x86)',
                os.environ.get('ProgramFiles', 'C:/Program Files'),
                os.environ.get('ProgramFiles(x86)', 'C:/Program Files (x86)')
            ]
            
            for program_dir in program_dirs:
                if os.path.exists(program_dir):
                    for root, dirs, files in os.walk(program_dir):
                        for file in files:
                            if file.lower().endswith('.exe'):
                                try:
                                    app_name = Path(file).stem.lower()
                                    if app_name not in apps and len(app_name) > 2:  # Skip very short names
                                        apps[app_name] = os.path.join(root, file)
                                except Exception:
                                    continue
                        # Limit depth to avoid too many files
                        if root.count(os.sep) - program_dir.count(os.sep) > 2:
                            dirs[:] = []
                            
        except Exception:
            pass
        
        return apps
    
    def _find_main_exe(self, install_location: str) -> Optional[str]:
        """Find the main executable in an install location"""
        if not install_location or not os.path.exists(install_location):
            return None
            
        try:
            # Common executable names to look for
            common_exes = ['main.exe', 'app.exe', 'program.exe', f"{Path(install_location).name}.exe"]
            
            for exe_name in common_exes:
                exe_path = os.path.join(install_location, exe_name)
                if os.path.exists(exe_path):
                    return exe_path
            
            # Look for any .exe file in the root directory
            for file in os.listdir(install_location):
                if file.lower().endswith('.exe'):
                    return os.path.join(install_location, file)
                    
        except Exception:
            pass
        
        return None
    
    def _load_file_handlers(self) -> Dict[str, str]:
        """Load file extension handlers"""
        if sys.platform == 'win32':
            return {
                '.txt': 'notepad.exe',
                '.pdf': 'AcroExch.Document.DC',
                '.doc': 'WINWORD.EXE',
                '.xlsx': 'EXCEL.EXE',
                '.py': 'code.exe',
                '.html': 'chrome.exe',
            }
        else:
            return {
                '.txt': 'gedit',
                '.pdf': 'evince',
                '.py': 'code',
                '.html': 'firefox',
            }
    
    def open_app(self, app_name: str) -> Dict[str, str]:
        """
        Open an application by name
        
        Args:
            app_name: Name of the application to open
            
        Returns:
            Dictionary with success status and message
        """
        app_name = app_name.lower().strip()
        
        # Check if app exists in common apps
        if app_name in self.common_apps:
            app_path = self.common_apps[app_name]
            try:
                if sys.platform == 'win32':
                    if app_name == 'settings':
                        os.startfile(app_path)
                    elif app_path.endswith('.lnk'):
                        # Handle shortcut files
                        os.startfile(app_path)
                    elif app_path.endswith('.exe') or os.path.exists(app_path):
                        # Handle executable files
                        subprocess.Popen([app_path], shell=True)
                    else:
                        # Try to find in PATH
                        subprocess.Popen(app_path, shell=True)
                elif sys.platform == 'darwin':
                    subprocess.Popen(['open', '-a', app_path])
                else:  # Linux
                    subprocess.Popen([app_path])
                
                return {
                    'success': True,
                    'message': f'Opened {app_name}',
                    'app': app_name
                }
            except Exception as e:
                return {
                    'success': False,
                    'message': f'Failed to open {app_name}: {str(e)}',
                    'app': app_name
                }
        else:
            # Try fuzzy matching for app names
            matched_app = self._find_app_by_fuzzy_match(app_name)
            if matched_app:
                return self.open_app(matched_app)
            
            # Try to find and open as direct application path
            available_apps = list(self.common_apps.keys())[:10]  # Show first 10 apps
            return {
                'success': False,
                'message': f'Application "{app_name}" not found. Available apps: {", ".join(available_apps)}... (Total: {len(self.common_apps)} apps discovered)',
                'app': app_name
            }
    
    def _find_app_by_fuzzy_match(self, app_name: str) -> Optional[str]:
        """Find app by fuzzy matching the name"""
        app_name = app_name.lower()
        
        # Exact substring match
        for known_app in self.common_apps.keys():
            if app_name in known_app or known_app in app_name:
                return known_app
        
        # Word-based matching
        app_words = set(app_name.split())
        for known_app in self.common_apps.keys():
            known_words = set(known_app.split())
            if app_words & known_words:  # Intersection of words
                return known_app
        
        return None
    
    def open_file(self, file_path: str) -> Dict[str, str]:
        """
        Open a file with its default handler
        
        Args:
            file_path: Path to the file to open
            
        Returns:
            Dictionary with success status and message
        """
        file_path = file_path.strip().strip('"\'')
        
        # Check if file exists
        if not os.path.exists(file_path):
            return {
                'success': False,
                'message': f'File not found: {file_path}',
                'file': file_path
            }
        
        try:
            if sys.platform == 'win32':
                os.startfile(file_path)
            elif sys.platform == 'darwin':
                subprocess.Popen(['open', file_path])
            else:  # Linux
                subprocess.Popen(['xdg-open', file_path])
            
            return {
                'success': True,
                'message': f'Opened file: {os.path.basename(file_path)}',
                'file': file_path
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Failed to open file: {str(e)}',
                'file': file_path
            }
    
    def open_folder(self, folder_path: str) -> Dict[str, str]:
        """
        Open a folder in file explorer
        
        Args:
            folder_path: Path to the folder to open
            
        Returns:
            Dictionary with success status and message
        """
        folder_path = folder_path.strip().strip('"\'')
        
        # Check if folder exists
        if not os.path.isdir(folder_path):
            return {
                'success': False,
                'message': f'Folder not found: {folder_path}',
                'folder': folder_path
            }
        
        try:
            if sys.platform == 'win32':
                os.startfile(folder_path)
            elif sys.platform == 'darwin':
                subprocess.Popen(['open', folder_path])
            else:  # Linux
                subprocess.Popen(['nautilus', folder_path])
            
            return {
                'success': True,
                'message': f'Opened folder: {os.path.basename(folder_path)}',
                'folder': folder_path
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Failed to open folder: {str(e)}',
                'folder': folder_path
            }
    
    def open_url(self, url: str) -> Dict[str, str]:
        """
        Open a URL in default browser
        
        Args:
            url: URL to open
            
        Returns:
            Dictionary with success status and message
        """
        url = url.strip()
        
        # Add protocol if missing
        if not url.startswith(('http://', 'https://', 'ftp://')):
            url = 'https://' + url
        
        try:
            if sys.platform == 'win32':
                os.startfile(url)
            elif sys.platform == 'darwin':
                subprocess.Popen(['open', url])
            else:  # Linux
                subprocess.Popen(['xdg-open', url])
            
            return {
                'success': True,
                'message': f'Opened URL: {url}',
                'url': url
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Failed to open URL: {str(e)}',
                'url': url
            }
    
    def get_common_apps(self) -> List[str]:
        """Get list of available common applications"""
        return list(self.common_apps.keys())
    
    def list_recent_files(self, limit: int = 10) -> List[str]:
        """
        List recently opened files
        
        Args:
            limit: Maximum number of files to return
            
        Returns:
            List of recent file paths
        """
        recent_files = []
        
        if sys.platform == 'win32':
            recent_path = Path.home() / 'AppData/Roaming/Microsoft/Windows/Recent'
        elif sys.platform == 'darwin':
            recent_path = Path.home() / 'Library/Recent Places.items'
        else:
            recent_path = Path.home() / '.recently-used'
        
        if recent_path.exists():
            try:
                files = sorted(
                    recent_path.iterdir(),
                    key=lambda x: x.stat().st_mtime,
                    reverse=True
                )
                recent_files = [str(f) for f in files[:limit]]
            except Exception:
                pass
        
        return recent_files
