import os
import sys
import httpx
import subprocess
import asyncio
from pathlib import Path
from settings_manager import APP_VERSION

GITHUB_REPO = "Nanaconda38/valorant_tracker"
TEMP_INSTALLER_NAME = "ValorantTrackerSetup_Update.exe"

class AppUpdater:
    def __init__(self) -> None:
        self.download_progress = 0
        self.download_task = None
        # Save installer in the system temp directory
        self.installer_path = Path(os.environ.get("TEMP", ".")) / TEMP_INSTALLER_NAME

    async def check_latest_release(self) -> dict:
        """
        Queries the GitHub Releases API for the latest version.
        """
        url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
        headers = {"User-Agent": "ValorantTracker-Updater"}
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.get(url, headers=headers)
                if resp.status_code != 200:
                    return {"error": f"GitHub API returned status {resp.status_code}"}
                
                data = resp.json()
                latest_version = data.get("tag_name", "").replace("v", "").strip()
                
                # Compare versions
                update_available = self.is_newer(APP_VERSION, latest_version)
                
                # Find the setup executable asset
                download_url = None
                for asset in data.get("assets", []):
                    name = asset.get("name", "")
                    if name.endswith(".exe") and "setup" in name.lower():
                        download_url = asset.get("browser_download_url")
                        break
                
                # Fallback to first .exe if no "setup" keyword
                if not download_url:
                    for asset in data.get("assets", []):
                        if asset.get("name", "").endswith(".exe"):
                            download_url = asset.get("browser_download_url")
                            break

                return {
                    "current_version": APP_VERSION,
                    "latest_version": latest_version,
                    "update_available": update_available and bool(download_url),
                    "download_url": download_url,
                    "release_notes": data.get("body", "")
                }
            except Exception as e:
                return {"error": str(e)}

    def is_newer(self, current: str, latest: str) -> bool:
        """
        Compares version strings. Returns True if latest is newer than current.
        """
        try:
            curr_parts = [int(x) for x in current.split(".")]
            lat_parts = [int(x) for x in latest.split(".")]
            # pad to same length
            while len(curr_parts) < len(lat_parts):
                curr_parts.append(0)
            while len(lat_parts) < len(curr_parts):
                lat_parts.append(0)
            return lat_parts > curr_parts
        except ValueError:
            return latest != current

    async def download_installer(self, download_url: str) -> None:
        """
        Downloads the latest installer executable in chunks and tracks progress.
        """
        self.download_progress = 0
        headers = {"User-Agent": "ValorantTracker-Updater"}
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                async with client.stream("GET", download_url, headers=headers) as response:
                    if response.status_code != 200:
                        raise RuntimeError(f"Download failed: status {response.status_code}")
                    
                    total_bytes = int(response.headers.get("content-length", 0))
                    bytes_downloaded = 0
                    
                    # Ensure directory exists
                    self.installer_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    with open(self.installer_path, "wb") as f:
                        async for chunk in response.iter_bytes(chunk_size=16384):
                            f.write(chunk)
                            bytes_downloaded += len(chunk)
                            if total_bytes > 0:
                                self.download_progress = int((bytes_downloaded / total_bytes) * 100)
                    self.download_progress = 100
            except Exception as e:
                self.download_progress = -1
                raise e

    def run_installer_and_exit(self) -> bool:
        """
        Launches the downloaded installer detached from the current process and exits.
        """
        if not self.installer_path.exists():
            return False
            
        # Spawn the setup installer
        # /SILENT runs the installer without manual confirmations (shows progress bar).
        # /SUPPRESSMSGBOXES suppresses popup errors.
        # CloseApplications=yes in ISS shuts down the app automatically.
        creationflags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
        subprocess.Popen(
            [str(self.installer_path), "/SILENT", "/SUPPRESSMSGBOXES"],
            creationflags=creationflags,
            close_fds=True
        )
        sys.exit(0)
