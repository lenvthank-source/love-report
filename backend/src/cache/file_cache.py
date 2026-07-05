import hashlib
import json
from pathlib import Path
from typing import Any, Optional

class FileCache:
    def __init__(self, cache_dir: str = ".cache"):
        """Initializes the file cache in the specified directory."""
        # Ensure we place the cache dir relative to the project root or absolute path
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _compute_hash(self, payload: Any) -> str:
        """Computes SHA-256 hash of a JSON-serializable payload."""
        # Sort keys to ensure deterministic hashing for identical dictionary inputs
        serialized = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def _get_cache_path(self, payload: Any) -> Path:
        """Gets the path to the cached file for the given payload."""
        file_hash = self._compute_hash(payload)
        return self.cache_dir / f"{file_hash}.json"

    def get(self, payload: Any) -> Optional[Any]:
        """Retrieves cached data for the payload if it exists, otherwise returns None."""
        cache_path = self._get_cache_path(payload)
        if cache_path.exists():
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return None
        return None

    def set(self, payload: Any, data: Any) -> None:
        """Caches the given data associated with the payload."""
        cache_path = self._get_cache_path(payload)
        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
