"""Config holders, optionally reloading the file when it changes."""

import sys
import threading
from pathlib import Path

from mockapi.config import Config, ConfigError, load_config
from mockapi.router import Router


class StaticConfig:
    def __init__(self, config: Config):
        self._router = Router(config.routes)
        self._headers = config.headers

    def current(self) -> tuple[Router, dict]:
        return self._router, self._headers


class WatchedConfig(StaticConfig):
    """Reload the config on the next request after the file was modified.

    If the new file is invalid, the previous config stays active.
    """

    def __init__(self, path: Path, config: Config):
        super().__init__(config)
        self.path = Path(path)
        self._mtime = self._stat()
        self._lock = threading.Lock()

    def _stat(self) -> float | None:
        try:
            return self.path.stat().st_mtime
        except OSError:
            return None

    def current(self) -> tuple[Router, dict]:
        mtime = self._stat()
        if mtime is not None and mtime != self._mtime:
            with self._lock:
                if mtime != self._mtime:
                    self._mtime = mtime
                    self._reload()
        return super().current()

    def _reload(self) -> None:
        try:
            config = load_config(self.path)
        except ConfigError as exc:
            print(f"reload failed, keeping previous config: {exc}", file=sys.stderr)
            return
        self._router = Router(config.routes)
        self._headers = config.headers
        print(f"config reloaded: {len(config.routes)} route(s)")
