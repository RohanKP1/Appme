import os
import shutil

class DesktopEntry:
    def __init__(self, name, comment, exec_command, icon, terminal=False, categories=None, url="", browser_medium="", browser_id="", browser_name="", isolated=False):
        self.name = name
        self.comment = comment
        self.exec_command = exec_command
        self.icon = icon
        self.terminal = terminal
        self.categories = categories or ["Network"]
        
        self.url = url
        self.browser_medium = browser_medium
        self.browser_id = browser_id       
        self.browser_name = browser_name   
        self.isolated = isolated

    @staticmethod
    def get_browsers_robust():
        browsers = {"System": [], "Flatpak": [], "Snap": []}
        desktop_paths = [
            "/usr/share/applications",
            "/usr/local/share/applications",
            os.path.expanduser("~/.local/share/applications"),
            "/var/lib/flatpak/exports/share/applications",
            "/var/lib/snapd/desktop/applications",
            # Sandbox paths
            "/run/host/usr/share/applications",
            "/run/host/usr/local/share/applications",
            "/run/host/var/lib/flatpak/exports/share/applications",
            "/run/host/var/lib/snapd/desktop/applications"
        ]
        
        seen_ids = set()
        
        for path in desktop_paths:
            if not os.path.exists(path):
                continue
                
            for filename in os.listdir(path):
                if filename.endswith(".desktop"):
                    full_path = os.path.join(path, filename)
                    try:
                        with open(full_path, 'r', errors='ignore') as f:
                            content = f.read()
                            if "Categories=" in content and "WebBrowser" in content:
                                browser_id = filename.replace(".desktop", "")
                                if browser_id in seen_ids:
                                    continue
                                
                                display_name = browser_id
                                for line in content.splitlines():
                                    if line.startswith("Name="):
                                        display_name = line.split("=", 1)[1].strip()
                                        break

                                browser_data = {"id": browser_id, "name": display_name}
                                
                                if "flatpak" in full_path:
                                    browsers["Flatpak"].append(browser_data)
                                elif "snap" in full_path:
                                    browsers["Snap"].append(browser_data)
                                else:
                                    browsers["System"].append(browser_data)
                                    
                                seen_ids.add(browser_id)
                    except Exception:
                        continue
 
        for key in browsers:
            browsers[key] = sorted(browsers[key], key=lambda x: x["name"].lower())
            
        return browsers

    @staticmethod
    def generate_exec_command(medium, browser_id, url, name, isolated=False):
        browser_id_lower = browser_id.lower()
        cmd_args = ""
        profile_flag = ""
        
        # --- ISOLATION LOGIC ---
        if isolated:
            safe_name = name.lower().replace(' ', '_').replace('/', '')
            profile_dir = os.path.expanduser(f"~/.local/share/Appme/profiles/{safe_name}")
            os.makedirs(profile_dir, exist_ok=True)
            
            chromium_variants = ["chrome", "chromium", "brave", "msedge", "msedge-beta", "msedge-dev", "opera", "vivaldi", "chromium-browser"]
            if any(v in browser_id_lower for v in chromium_variants):
                profile_flag = f" --user-data-dir=\"{profile_dir}\""
            elif any(v in browser_id_lower for v in ["firefox", "librewolf", "waterfox", "mozilla-firefox"]):
                profile_flag = f" --profile \"{profile_dir}\" --no-remote"
            elif "epiphany" in browser_id_lower or "org.gnome.epiphany" in browser_id_lower:
                profile_flag = f" --profile=\"{profile_dir}\""

        # --- EXECUTION LOGIC ---
        if "epiphany" in browser_id_lower or "org.gnome.epiphany" in browser_id_lower:
            cmd_args = f"--application-mode=\"{url}\"{profile_flag}"
        else:
            chromium_variants = ["chrome", "chromium", "brave", "msedge", "msedge-beta", "msedge-dev", "opera", "vivaldi", "chromium-browser"]
            if any(v in browser_id_lower for v in chromium_variants):
                cmd_args = f"--app={url}{profile_flag}"
            elif any(v in browser_id_lower for v in ["firefox", "librewolf", "waterfox", "mozilla-firefox"]):
                cmd_args = f"--new-window {url}{profile_flag}"
            else:
                cmd_args = f"{url}{profile_flag}"

        medium = medium.lower()
        if medium == "system":
            return f"{browser_id} {cmd_args}"
        elif medium == "flatpak":
            return f"flatpak run {browser_id} {cmd_args}"
        elif medium == "snap":
            return f"snap run {browser_id} {cmd_args}"
        else:
            return f"{browser_id} {url}"

    def generate_dotdesktop_file(self):
        return f"""[Desktop Entry]
Version=1.0
Type=Application
Name={self.name}
Comment={self.comment}
Exec={self.exec_command}
Icon={self.icon}
Terminal={str(self.terminal).lower()}
Categories={';'.join(self.categories)};
X-WebApp-URL={self.url}
X-WebApp-BrowserMedium={self.browser_medium}
X-WebApp-BrowserID={self.browser_id}
X-WebApp-BrowserName={self.browser_name}
X-WebApp-Isolated={str(self.isolated).lower()}
"""

    def export_dotdesktop_file(self):
        apps_dir = os.path.expanduser("~/.local/share/applications")
        os.makedirs(apps_dir, exist_ok=True)
        filename = f"webapp_{self.name.lower().replace(' ', '_')}.desktop"
        filepath = os.path.join(apps_dir, filename)
        
        with open(filepath, 'w') as f:
            f.write(self.generate_dotdesktop_file())

    @staticmethod
    def delete_webapp(filepath, name=None):
        if os.path.exists(filepath):
            os.remove(filepath)
        
        if name:
            safe_name = name.lower().replace(' ', '_').replace('/', '')
            profile_dir = os.path.expanduser(f"~/.local/share/Appme/profiles/{safe_name}")
            if os.path.exists(profile_dir):
                shutil.rmtree(profile_dir)

    @staticmethod
    def get_user_webapps():
        apps_dir = os.path.expanduser("~/.local/share/applications")
        webapps = []
        
        if not os.path.exists(apps_dir):
            return webapps
            
        for filename in os.listdir(apps_dir):
            if filename.startswith("webapp_") and filename.endswith(".desktop"):
                filepath = os.path.join(apps_dir, filename)
                try:
                    with open(filepath, 'r', errors='ignore') as f:
                        content = f.read()
                        
                        if "Categories=" in content and "WebApp" in content:
                            app_data = {
                                "name": filename.replace(".desktop", ""),
                                "icon": "applications-internet-symbolic",
                                "url": "",
                                "category": "Network",
                                "browser_medium": "System",
                                "browser_id": "xdg-open",
                                "browser_name": "System Browser",
                                "isolated": False,
                                "filename": filename,
                                "filepath": filepath
                            }
                            
                            for line in content.splitlines():
                                if line.startswith("Name="): app_data["name"] = line.split("=", 1)[1].strip()
                                elif line.startswith("Icon="): app_data["icon"] = line.split("=", 1)[1].strip()
                                elif line.startswith("X-WebApp-URL="): app_data["url"] = line.split("=", 1)[1].strip()
                                elif line.startswith("X-WebApp-BrowserMedium="): app_data["browser_medium"] = line.split("=", 1)[1].strip()
                                elif line.startswith("X-WebApp-BrowserID="): app_data["browser_id"] = line.split("=", 1)[1].strip()
                                elif line.startswith("X-WebApp-BrowserName="): app_data["browser_name"] = line.split("=", 1)[1].strip()
                                elif line.startswith("X-WebApp-Isolated="): app_data["isolated"] = line.split("=", 1)[1].strip().lower() == "true"
                                elif line.startswith("Categories="):
                                    cats = line.split("=", 1)[1].strip().split(";")
                                    if len(cats) > 1 and cats[1]: app_data["category"] = cats[1]
                                    
                            webapps.append(app_data)
                except Exception:
                    continue
                    
        return sorted(webapps, key=lambda x: x['name'].lower())