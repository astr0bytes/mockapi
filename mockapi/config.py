"""Config file loading and validation."""

import json
from dataclasses import dataclass, field
from pathlib import Path

METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}


class ConfigError(Exception):
    pass


@dataclass
class Route:
    method: str
    path: str
    status: int = 200
    body: object = None
    body_file: str | None = None
    headers: dict = field(default_factory=dict)
    delay_ms: int = 0
    echo: bool = False


@dataclass
class Config:
    routes: list[Route]
    headers: dict


def _parse_route(index: int, raw: dict, base_dir: Path) -> Route:
    where = f"routes[{index}]"
    if "path" not in raw:
        raise ConfigError(f"{where}: missing 'path'")
    method = raw.get("method", "GET").upper()
    if method not in METHODS:
        raise ConfigError(f"{where}: unknown method '{method}'")
    if not raw["path"].startswith("/"):
        raise ConfigError(f"{where}: path must start with '/'")

    body_file = raw.get("body_file")
    if body_file:
        body_file = str((base_dir / body_file).resolve())
        if not Path(body_file).is_file():
            raise ConfigError(f"{where}: file not found {body_file}")

    known = set(Route.__dataclass_fields__) - {"method"}
    unknown = set(raw) - known - {"method"}
    if unknown:
        raise ConfigError(f"{where}: unknown fields {sorted(unknown)}")

    return Route(**{**raw, "method": method, "body_file": body_file})


def load_config(path: Path) -> Config:
    try:
        data = json.loads(Path(path).read_text())
    except FileNotFoundError:
        raise ConfigError(f"file not found: {path}") from None
    except json.JSONDecodeError as exc:
        raise ConfigError(f"invalid JSON: {exc}") from None

    routes = [_parse_route(i, r, Path(path).parent) for i, r in enumerate(data.get("routes", []))]
    if not routes:
        raise ConfigError("no routes defined")
    return Config(routes=routes, headers=data.get("headers", {}))
