import os
import base64

from app_logging import get_logger


logger = get_logger(__name__)

class LockfileScanner:
    """
    Scans and reads the Riot client lockfile to retrieve connection details.
    """

    def __init__(self):
        """
        Initializes the LockfileScanner.
        """
        pass

    def scan(self) -> dict:
        """
        Scans for the lockfile and returns the credentials.

        @return: A dictionary containing port, protocol, and auth headers, or None if not found.
        """
        local_app_data = os.environ.get("LOCALAPPDATA", "")
        if not local_app_data:
            return None
        
        lockfile_path = os.path.join(
            local_app_data, "Riot Games", "Riot Client", "Config", "lockfile"
        )
        
        if not os.path.exists(lockfile_path):
            return None
            
        try:
            with open(lockfile_path, "r", encoding="utf-8") as f:
                content = f.read()
            parts = content.split(":")
            if len(parts) >= 5:
                port = int(parts[2])
                password = parts[3]
                protocol = parts[4]
                
                auth_str = f"riot:{password}"
                auth_bytes = auth_str.encode("utf-8")
                base64_auth = base64.b64encode(auth_bytes).decode("utf-8")
                
                return {
                    "port": port,
                    "protocol": protocol,
                    "headers": {
                        "Authorization": f"Basic {base64_auth}",
                        "Accept": "application/json"
                    }
                }
        except Exception:
            logger.debug("Unable to read Riot lockfile", exc_info=True)
            return None
            
        return None
