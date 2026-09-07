"""Route matching, path parameters and body templating."""

import json
import re
from dataclasses import dataclass

from mockapi.config import Route

_PARAM_RE = re.compile(r"\{(\w+)\}")
_PLACEHOLDER_RE = re.compile(r"\{\{\s*(\w+)\.(\w+)\s*\}\}")


@dataclass
class Match:
    route: Route
    params: dict[str, str]


def compile_path(path: str) -> re.Pattern:
    """'/users/{id}' -> regex with a named group 'id'. A trailing '*' matches anything."""
    pattern = ""
    pos = 0
    for m in _PARAM_RE.finditer(path):
        pattern += re.escape(path[pos:m.start()]) + f"(?P<{m.group(1)}>[^/]+)"
        pos = m.end()
    tail = path[pos:]
    if tail.endswith("*"):
        pattern += re.escape(tail[:-1]) + ".*"
    else:
        pattern += re.escape(tail)
    return re.compile(f"^{pattern}/?$")


class Router:
    def __init__(self, routes: list[Route]):
        self._routes = [(compile_path(r.path), r) for r in routes]

    def match(self, method: str, path: str) -> Match | None:
        for regex, route in self._routes:
            if route.method == method and (m := regex.match(path)):
                return Match(route, m.groupdict())
        return None

    def allowed_methods(self, path: str) -> list[str]:
        return sorted({r.method for regex, r in self._routes if regex.match(path)})


def render_body(body, context: dict) -> object:
    """Replace {{params.id}} / {{query.page}} placeholders in body strings."""

    def substitute(text: str) -> str:
        def repl(m):
            value = context.get(m.group(1), {}).get(m.group(2))
            return str(value) if value is not None else m.group(0)
        return _PLACEHOLDER_RE.sub(repl, text)

    if isinstance(body, str):
        return substitute(body)
    if isinstance(body, list):
        return [render_body(item, context) for item in body]
    if isinstance(body, dict):
        return {k: render_body(v, context) for k, v in body.items()}
    return body


def serialize(body) -> tuple[bytes, str]:
    if body is None:
        return b"", "text/plain"
    if isinstance(body, str):
        return body.encode(), "text/plain; charset=utf-8"
    return json.dumps(body, ensure_ascii=False).encode(), "application/json"
