import base64
import ctypes
import os
from ctypes import wintypes
from pathlib import Path

from app_paths import runtime_path


HENRIK_SECRET_FILENAME = "henrik_api_key.dpapi"
FALLBACK_SECRET_FILENAME = "henrik_api_key.local"


class SecretStorageError(RuntimeError):
    """
    Raised when a local secret cannot be saved or loaded.
    """


class DATA_BLOB(ctypes.Structure):
    _fields_ = [
        ("cbData", wintypes.DWORD),
        ("pbData", ctypes.POINTER(ctypes.c_char)),
    ]


class HenrikSecretManager:
    """
    Stores the HenrikDev API key in the current Windows user profile.
    """

    def __init__(self, secret_path: str | Path | None = None):
        """
        Initializes the secret manager.

        @param secret_path: Optional storage path, useful for tests.
        """
        self.secret_path = Path(secret_path) if secret_path else runtime_path(HENRIK_SECRET_FILENAME)
        self.fallback_path = self.secret_path.with_name(FALLBACK_SECRET_FILENAME)

    def has_key(self) -> bool:
        """
        Returns True when a HenrikDev key is available from secure storage or dev env.
        """
        return bool(self.get_key())

    def get_key(self) -> str | None:
        """
        Returns the HenrikDev key from secure storage, fallback storage, or dev env.
        """
        stored = self._read_stored_key()
        if stored:
            return stored
        env_key = os.getenv("HENRIK_API_KEY", "").strip()
        return env_key or None

    def set_key(self, api_key: str) -> None:
        """
        Saves a HenrikDev key to secure local storage.
        """
        cleaned_key = (api_key or "").strip()
        if not cleaned_key:
            raise ValueError("HenrikDev API key cannot be empty.")

        self.secret_path.parent.mkdir(parents=True, exist_ok=True)
        if self._dpapi_available():
            encrypted = self._protect(cleaned_key.encode("utf-8"))
            self.secret_path.write_bytes(encrypted)
            if self.fallback_path.exists():
                self.fallback_path.unlink()
            return

        # Temporary non-Windows/dev fallback. Do not use for distributed Windows builds.
        encoded = base64.b64encode(cleaned_key.encode("utf-8"))
        self.fallback_path.write_bytes(encoded)

    def delete_key(self) -> None:
        """
        Deletes the locally stored HenrikDev key.
        """
        for path in [self.secret_path, self.fallback_path]:
            try:
                path.unlink()
            except FileNotFoundError:
                pass

    def storage_status(self) -> dict:
        """
        Returns non-sensitive information about secret storage.
        """
        stored_secure = self.secret_path.exists()
        stored_fallback = self.fallback_path.exists()
        env_available = bool(os.getenv("HENRIK_API_KEY", "").strip())
        return {
            "has_key": bool(self.get_key()),
            "stored_securely": stored_secure and self._dpapi_available(),
            "stored_with_fallback": stored_fallback,
            "env_available": env_available,
            "storage": "dpapi" if stored_secure else "fallback" if stored_fallback else "env" if env_available else "none",
        }

    def _read_stored_key(self) -> str | None:
        """
        Reads a key from local storage without consulting environment variables.
        """
        if self.secret_path.exists():
            if not self._dpapi_available():
                raise SecretStorageError("DPAPI secret exists but DPAPI is unavailable on this platform.")
            decrypted = self._unprotect(self.secret_path.read_bytes())
            return decrypted.decode("utf-8").strip() or None

        if self.fallback_path.exists():
            try:
                return base64.b64decode(self.fallback_path.read_bytes()).decode("utf-8").strip() or None
            except Exception as exc:
                raise SecretStorageError("Fallback HenrikDev key storage is unreadable.") from exc
        return None

    def _dpapi_available(self) -> bool:
        """
        Returns True when Windows DPAPI can be used.
        """
        return os.name == "nt" and hasattr(ctypes, "windll")

    def _protect(self, secret: bytes) -> bytes:
        """
        Encrypts bytes with Windows DPAPI for the current user.
        """
        in_blob, in_buffer = self._blob_from_bytes(secret)
        out_blob = DATA_BLOB()
        try:
            _ = in_buffer
            if not ctypes.windll.crypt32.CryptProtectData(
                ctypes.byref(in_blob),
                "ValorantTracker HenrikDev API key",
                None,
                None,
                None,
                0,
                ctypes.byref(out_blob),
            ):
                raise SecretStorageError("Unable to protect HenrikDev API key with DPAPI.")
            return ctypes.string_at(out_blob.pbData, out_blob.cbData)
        finally:
            if out_blob.pbData:
                ctypes.windll.kernel32.LocalFree(out_blob.pbData)

    def _unprotect(self, encrypted: bytes) -> bytes:
        """
        Decrypts bytes with Windows DPAPI for the current user.
        """
        in_blob, in_buffer = self._blob_from_bytes(encrypted)
        out_blob = DATA_BLOB()
        try:
            _ = in_buffer
            if not ctypes.windll.crypt32.CryptUnprotectData(
                ctypes.byref(in_blob),
                None,
                None,
                None,
                None,
                0,
                ctypes.byref(out_blob),
            ):
                raise SecretStorageError("Unable to read HenrikDev API key from DPAPI.")
            return ctypes.string_at(out_blob.pbData, out_blob.cbData)
        finally:
            if out_blob.pbData:
                ctypes.windll.kernel32.LocalFree(out_blob.pbData)

    def _blob_from_bytes(self, value: bytes) -> tuple[DATA_BLOB, ctypes.Array]:
        """
        Creates a DATA_BLOB from bytes for DPAPI calls.
        """
        buffer = ctypes.create_string_buffer(value)
        blob = DATA_BLOB(len(value), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_char)))
        return blob, buffer
