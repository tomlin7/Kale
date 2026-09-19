#!/usr/bin/env python3
"""Kale Reference Registry Server runner.

Usage:
    python tools/registry/server.py [--host 0.0.0.0] [--port 8080] [--storage-dir .kale_registry]
"""

import sys
import argparse
from kale.pm.registry import RegistryServer, DEFAULT_REGISTRY_URL


def main():
    parser = argparse.ArgumentParser(description="Kale Package Registry Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host address to bind (default: 0.0.0.0)")
    parser.add_argument("-p", "--port", type=int, default=8080, help="Port number (default: 8080)")
    parser.add_argument("--storage-dir", default=".kale_registry", help="Directory for storing packages and index")
    parser.add_argument("--require-auth", action="store_true", help="Require Bearer token authentication for publish")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose HTTP request logging")

    args = parser.parse_args()

    print(f"Starting Kale Package Registry on {args.host}:{args.port}...")
    print(f"Package storage directory: {args.storage_dir}")
    server = RegistryServer(
        host=args.host,
        port=args.port,
        storage_dir=args.storage_dir,
        require_auth=args.require_auth,
        verbose=args.verbose or True,
    )

    try:
        print(f"Registry ready at http://{args.host}:{args.port}")
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down registry...")
        server.stop()
        return 0


if __name__ == "__main__":
    sys.exit(main())
