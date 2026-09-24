#!/usr/bin/env python3
"""mockapi - mock HTTP API server driven by a JSON file."""

import argparse
import sys
from pathlib import Path

from mockapi import __version__
from mockapi.config import ConfigError, load_config
from mockapi.server import serve
from mockapi.watch import StaticConfig, WatchedConfig


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mockapi", description=__doc__)
    parser.add_argument("config", type=Path, help="JSON routes file")
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("-p", "--port", type=int, default=8080)
    parser.add_argument("--cors", action="store_true", help="add permissive CORS headers")
    parser.add_argument("--check", action="store_true", help="validate the config and exit")
    parser.add_argument("--watch", action="store_true", help="reload the config when the file changes")
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        config = load_config(args.config)
    except ConfigError as exc:
        print(f"Invalid config: {exc}", file=sys.stderr)
        return 1

    if args.check:
        print(f"OK: {len(config.routes)} route(s)")
        for route in config.routes:
            print(f"  {route.method:7} {route.path}")
        return 0

    source = WatchedConfig(args.config, config) if args.watch else StaticConfig(config)
    serve(source, args.host, args.port, cors=args.cors)
    return 0


if __name__ == "__main__":
    sys.exit(main())
