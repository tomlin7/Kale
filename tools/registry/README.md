# Kale Package Registry & Publishing Platform

Lightweight, secure, high-performance package registry platform and reference server for the Kale programming language ecosystem, inspired by npm and PyPI.

## 🚀 Readiness & Availability Status

- **Current State (Ready Now)**:
  - The Kale package manager (`kale.toml`, `kale new`, `kale init`, `kale add`, `kale remove`, `kale run`, `kale build`, `kale pack`) is fully operational.
  - The reference registry platform is ready and functional immediately for local teams, CI/CD pipelines, and self-hosted on-premise infrastructure.
  - Endpoints implement npm- and PyPI-inspired package publishing, semantic versioning, reproducible `.kale-pkg` archives, token authentication, and metadata search.
- **Roadmap & Public Cloud Rollout**:
  - **Phase 1 (Complete)**: Reference server implementation, CLI client integration (`kale publish`, `kale search`, `kale info`, `kale login`, `kale whoami`), reproducible tar.gz packaging with fixed pax timestamps, and path-traversal hardened file storage.
  - **Phase 2 (Q4 2026)**: Public community registry hosting (`https://registry.kale-lang.org`), multi-tenant GitHub OAuth integration, scoped packages (`@scope/package`), and CDN-cached package tarball distribution.

## Features
- **Publish packages**: `POST /api/v1/packages/publish` accepts bit-for-bit reproducible `.kale-pkg` archives with SHA-256 checksum verification and directory traversal protection.
- **List & search registry**: `GET /api/v1/packages` and `GET /api/v1/search?q=<query>` returns matching packages.
- **Package Metadata**: `GET /api/v1/packages/<name>` and `GET /api/v1/packages/<name>/<version>`.
- **Download Tarballs**: `GET /api/v1/packages/<name>/download/<version>`.
- **Authentication**: `POST /api/v1/auth/login`, `GET /api/v1/auth/whoami`, and Bearer token verification.

## Running the Registry Server

```bash
# Via Python runner
python tools/registry/server.py --port 8080 --storage-dir .kale_registry

# Or directly via Kale CLI
kale registry start --port 8080
```

## CLI Commands

### Initialize or bootstrap a project
```bash
kale new my_app          # Creates application project with kale.toml, src/main.kl, .gitignore, README.md
kale new my_lib --lib    # Creates library project with kale.toml and src/lib.kl
kale init                # Initializes kale.toml in current directory
```

### Dependency management
```bash
kale add http                     # Automatically queries registry for latest version constraint
kale add my_lib --path ../my_lib  # Adds local path dependency (supports transitive deps)
kale add test_framework --dev     # Adds development dependency
kale remove http                  # Removes dependency
```

### Build & Run
```bash
kale run                 # Runs start script or manifest entry
kale run custom_script   # Executes custom script defined in [scripts] with argument forwarding
kale build               # Compiles project binary based on kale.toml [build]
```

### Packaging & Publishing
```bash
# Create reproducible archive
kale pack

# Authenticate with registry
kale login --registry http://localhost:8080 -u myuser -p mypassword
kale whoami --registry http://localhost:8080

# Publish package
kale publish --registry http://localhost:8080

# Search & Inspect
kale search
kale search math
kale info math_utils
```
