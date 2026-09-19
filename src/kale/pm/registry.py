"""Package publishing registry client and reference registry server implementation.

Provides npm- and PyPI-inspired endpoints:
- POST /api/v1/packages/publish
- GET  /api/v1/packages/:name
- GET  /api/v1/packages/:name/:version
- GET  /api/v1/packages/:name/download/:version
- GET  /api/v1/search?q=:query
- POST /api/v1/auth/login
"""

import os
import sys
import json
import base64
import hashlib
import secrets
import threading
import tarfile
import re
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs, unquote
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from typing import Any, Dict, List, Optional, Tuple

try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib  # type: ignore
    except ImportError:
        tomllib = None

from .manifest import Manifest, find_manifest
from .pack import pack_project

DEFAULT_REGISTRY_URL = "http://localhost:8080"

SAFE_NAME_RE = re.compile(r"^[a-zA-Z0-9_-]+$")
SAFE_VERSION_RE = re.compile(r"^[a-zA-Z0-9._+-]+$")


def is_safe_name(name: str) -> bool:
    """Validates that package name contains only valid characters and no traversal."""
    return bool(SAFE_NAME_RE.match(name)) and not (".." in name or "/" in name or "\\" in name)


def is_safe_version(version: str) -> bool:
    """Validates that version string contains only valid characters and no traversal."""
    return bool(SAFE_VERSION_RE.match(version)) and not (".." in version or "/" in version or "\\" in version)


class RegistryConfig:
    """Manages local registry credentials and config (~/.kale/config.json)."""

    @staticmethod
    def _config_path() -> str:
        config_dir = os.environ.get("KALE_CONFIG_DIR") or os.path.expanduser("~/.kale")
        os.makedirs(config_dir, exist_ok=True)
        return os.path.join(config_dir, "config.json")

    @classmethod
    def load(cls) -> Dict[str, Any]:
        p = cls._config_path()
        if os.path.isfile(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    @classmethod
    def save(cls, data: Dict[str, Any]):
        p = cls._config_path()
        with open(p, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def get_default_registry(cls) -> str:
        if "KALE_REGISTRY_URL" in os.environ:
            return os.environ["KALE_REGISTRY_URL"].rstrip("/")
        cfg = cls.load()
        return cfg.get("default_registry", DEFAULT_REGISTRY_URL).rstrip("/")

    @classmethod
    def get_token(cls, registry_url: str) -> Optional[str]:
        if "KALE_REGISTRY_TOKEN" in os.environ:
            return os.environ["KALE_REGISTRY_TOKEN"]
        cfg = cls.load()
        registries = cfg.get("registries", {})
        norm = registry_url.rstrip("/")
        return registries.get(norm, {}).get("token")

    @classmethod
    def save_token(cls, registry_url: str, token: str):
        cfg = cls.load()
        norm = registry_url.rstrip("/")
        if "registries" not in cfg:
            cfg["registries"] = {}
        if norm not in cfg["registries"]:
            cfg["registries"][norm] = {}
        cfg["registries"][norm]["token"] = token
        cls.save(cfg)


class RegistryHandler(BaseHTTPRequestHandler):
    """HTTP handler implementing Kale Registry REST API."""

    server: "RegistryServer"  # Type hint

    def log_message(self, format: str, *args: Any):
        # Suppress noisy logging during standard tests
        if getattr(self.server, "verbose", False):
            super().log_message(format, *args)

    def _send_json(self, status: int, data: Any):
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_bytes(self, status: int, data: bytes, content_type: str = "application/octet-stream", filename: str = ""):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        if filename:
            self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.end_headers()
        self.wfile.write(data)

    def _read_json_body(self) -> Dict[str, Any]:
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length)
        if not raw:
            return {}
        return json.loads(raw.decode("utf-8"))

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        query = parse_qs(parsed.query)

        # GET /api/v1/health
        if path == "/api/v1/health":
            return self._send_json(200, {"status": "ok", "service": "kale-registry", "version": "1.0.0"})

        # GET /api/v1/auth/whoami or /api/v1/whoami
        if path in ("/api/v1/auth/whoami", "/api/v1/whoami"):
            auth = self.headers.get("Authorization", "")
            if auth.startswith("Bearer "):
                token = auth[len("Bearer "):].strip()
                user = self.server.token_users.get(token)
                if user:
                    return self._send_json(200, {"status": "ok", "authenticated": True, "username": user})
            if not self.server.require_auth:
                return self._send_json(200, {"status": "ok", "authenticated": True, "username": "guest"})
            return self._send_json(401, {"error": "Invalid or missing token.", "authenticated": False})

        # GET /api/v1/packages (list all packages)
        if path == "/api/v1/packages":
            results = self.server.search_packages("")
            return self._send_json(200, {"packages": results, "total": len(results)})

        # GET /api/v1/search?q=query
        if path == "/api/v1/search":
            q_list = query.get("q", [""])
            q = q_list[0].lower().strip()
            results = self.server.search_packages(q)
            return self._send_json(200, {"packages": results, "total": len(results)})

        # GET /api/v1/packages/:name/download/:version
        if "/download/" in path:
            prefix, version = path.rsplit("/download/", 1)
            if prefix.startswith("/api/v1/packages/"):
                pkg_name = prefix[len("/api/v1/packages/"):]
                if not is_safe_name(pkg_name) or not is_safe_version(version):
                    return self._send_json(400, {"error": "Invalid package name or version (traversal characters forbidden)."})
                archive_bytes, filename = self.server.get_package_archive(pkg_name, version)
                if archive_bytes is not None:
                    return self._send_bytes(200, archive_bytes, "application/gzip", filename=filename)
                return self._send_json(404, {"error": f"Package '{pkg_name}' version '{version}' not found."})

        # GET /api/v1/packages/:name or /api/v1/packages/:name/:version
        if path.startswith("/api/v1/packages/"):
            rest = path[len("/api/v1/packages/"):].split("/")
            pkg_name = rest[0]
            if not is_safe_name(pkg_name):
                return self._send_json(400, {"error": "Invalid package name (traversal characters forbidden)."})
            if len(rest) == 1:
                meta = self.server.get_package_index(pkg_name)
                if meta:
                    return self._send_json(200, meta)
                return self._send_json(404, {"error": f"Package '{pkg_name}' not found."})
            elif len(rest) == 2:
                version = rest[1]
                if not is_safe_version(version):
                    return self._send_json(400, {"error": "Invalid version (traversal characters forbidden)."})
                v_meta = self.server.get_version_metadata(pkg_name, version)
                if v_meta:
                    return self._send_json(200, v_meta)
                return self._send_json(404, {"error": f"Package '{pkg_name}' version '{version}' not found."})

        return self._send_json(404, {"error": f"Endpoint not found: {self.path}"})

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        # POST /api/v1/auth/login
        if path == "/api/v1/auth/login":
            body = self._read_json_body()
            username = body.get("username", "user")
            token = f"kale_pat_{secrets.token_hex(16)}"
            self.server.add_token(token, username)
            return self._send_json(200, {"status": "ok", "token": token, "username": username})

        # POST /api/v1/packages/publish
        if path == "/api/v1/packages/publish":
            # Check Bearer token if required
            auth = self.headers.get("Authorization", "")
            if self.server.require_auth:
                if not auth.startswith("Bearer "):
                    return self._send_json(401, {"error": "Missing or invalid Authorization header."})
                token = auth[len("Bearer "):].strip()
                if not self.server.validate_token(token):
                    return self._send_json(403, {"error": "Invalid or expired registry token."})

            body = self._read_json_body()
            name = body.get("name")
            version = body.get("version")
            checksum = body.get("checksum")
            archive_b64 = body.get("archive_base64")

            if not name or not version or not checksum or not archive_b64:
                return self._send_json(400, {"error": "Missing required fields: name, version, checksum, archive_base64"})

            if not is_safe_name(name):
                return self._send_json(400, {"error": f"Invalid package name '{name}'. Only alphanumeric characters, dashes, and underscores are allowed."})
            if not is_safe_version(version):
                return self._send_json(400, {"error": f"Invalid version string '{version}'. Traversal characters are forbidden."})

            try:
                archive_bytes = base64.b64decode(archive_b64)
            except Exception as e:
                return self._send_json(400, {"error": f"Invalid base64 archive data: {e}"})

            # Verify checksum
            actual_checksum = hashlib.sha256(archive_bytes).hexdigest()
            if actual_checksum != checksum:
                return self._send_json(400, {
                    "error": f"Checksum mismatch: expected {checksum}, got {actual_checksum}"
                })

            success, err_msg = self.server.publish_package(
                name=name,
                version=version,
                description=body.get("description", ""),
                authors=body.get("authors", []),
                license=body.get("license", "MIT"),
                dependencies=body.get("dependencies", {}),
                checksum=checksum,
                archive_bytes=archive_bytes,
            )

            if not success:
                return self._send_json(409, {"error": err_msg})

            return self._send_json(201, {
                "status": "success",
                "message": f"Successfully published {name}@{version}",
                "package": name,
                "version": version,
                "checksum": checksum,
            })

        return self._send_json(404, {"error": f"Endpoint not found: {self.path}"})


class RegistryServer(ThreadingHTTPServer):
    """Reference Registry Server for hosting and publishing Kale packages."""

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 8080,
        storage_dir: Optional[str] = None,
        require_auth: bool = False,
        verbose: bool = False,
    ):
        self.storage_dir = os.path.abspath(storage_dir or os.path.join(".", ".kale_registry"))
        self.packages_dir = os.path.join(self.storage_dir, "packages")
        self.index_dir = os.path.join(self.storage_dir, "index")
        os.makedirs(self.packages_dir, exist_ok=True)
        os.makedirs(self.index_dir, exist_ok=True)

        self.require_auth = require_auth
        self.verbose = verbose
        self.valid_tokens: set[str] = set()
        self.token_users: Dict[str, str] = {}
        self._thread: Optional[threading.Thread] = None

        super().__init__((host, port), RegistryHandler)

    @property
    def url(self) -> str:
        host, port = self.server_address
        return f"http://{host}:{port}"

    def add_token(self, token: str, username: str = "user"):
        self.valid_tokens.add(token)
        self.token_users[token] = username

    def validate_token(self, token: str) -> bool:
        if not self.require_auth:
            return True
        return token in self.valid_tokens

    def publish_package(
        self,
        name: str,
        version: str,
        description: str,
        authors: List[str],
        license: str,
        dependencies: Dict[str, Any],
        checksum: str,
        archive_bytes: bytes,
    ) -> Tuple[bool, Optional[str]]:
        if not is_safe_name(name):
            return False, f"Invalid package name '{name}'. Only alphanumeric characters, dashes, and underscores are allowed."
        if not is_safe_version(version):
            return False, f"Invalid version string '{version}'."

        pkg_version_dir = os.path.abspath(os.path.join(self.packages_dir, name, version))
        try:
            if os.path.commonpath([self.packages_dir, pkg_version_dir]) != self.packages_dir:
                return False, "Path traversal detected."
        except ValueError:
            return False, "Path traversal detected across drives."

        archive_filename = f"{name}-{version}.kale-pkg"
        archive_path = os.path.join(pkg_version_dir, archive_filename)

        if os.path.isfile(archive_path):
            return False, f"Version {version} of package '{name}' is already published."

        os.makedirs(pkg_version_dir, exist_ok=True)
        with open(archive_path, "wb") as f:
            f.write(archive_bytes)

        # Update package index
        index_file = os.path.abspath(os.path.join(self.index_dir, f"{name}.json"))
        try:
            if os.path.commonpath([self.index_dir, index_file]) != self.index_dir:
                return False, "Path traversal detected in package index."
        except ValueError:
            return False, "Path traversal detected across drives."
        now_iso = datetime.now(timezone.utc).isoformat()

        if os.path.isfile(index_file):
            with open(index_file, "r", encoding="utf-8") as f:
                index_data = json.load(f)
        else:
            index_data = {
                "name": name,
                "description": description,
                "authors": authors,
                "license": license,
                "latest": version,
                "versions": {},
            }

        index_data["description"] = description or index_data.get("description", "")
        index_data["latest"] = version
        index_data["versions"][version] = {
            "version": version,
            "description": description,
            "authors": authors,
            "license": license,
            "dependencies": dependencies,
            "checksum": checksum,
            "download_url": f"/api/v1/packages/{name}/download/{version}",
            "created_at": now_iso,
        }

        with open(index_file, "w", encoding="utf-8") as f:
            json.dump(index_data, f, indent=2)

        return True, None

    def get_package_index(self, name: str) -> Optional[Dict[str, Any]]:
        if not is_safe_name(name):
            return None
        index_file = os.path.abspath(os.path.join(self.index_dir, f"{name}.json"))
        try:
            if os.path.commonpath([self.index_dir, index_file]) != self.index_dir:
                return None
        except ValueError:
            return None
        if os.path.isfile(index_file):
            with open(index_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return None

    def get_version_metadata(self, name: str, version: str) -> Optional[Dict[str, Any]]:
        if not is_safe_name(name) or not is_safe_version(version):
            return None
        meta = self.get_package_index(name)
        if meta and "versions" in meta and version in meta["versions"]:
            return meta["versions"][version]
        return None

    def get_package_archive(self, name: str, version: str) -> Tuple[Optional[bytes], str]:
        if not is_safe_name(name) or not is_safe_version(version):
            return None, ""
        filename = f"{name}-{version}.kale-pkg"
        archive_path = os.path.abspath(os.path.join(self.packages_dir, name, version, filename))
        try:
            if os.path.commonpath([self.packages_dir, archive_path]) != self.packages_dir:
                return None, filename
        except ValueError:
            return None, filename
        if os.path.isfile(archive_path):
            with open(archive_path, "rb") as f:
                return f.read(), filename
        return None, filename

    def search_packages(self, query: str) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        if not os.path.isdir(self.index_dir):
            return results

        for fname in os.listdir(self.index_dir):
            if fname.endswith(".json"):
                p = os.path.join(self.index_dir, fname)
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        name = data.get("name", "")
                        desc = data.get("description", "")
                        if not query or query in name.lower() or query in desc.lower():
                            results.append({
                                "name": name,
                                "version": data.get("latest", ""),
                                "description": desc,
                                "license": data.get("license", "MIT"),
                            })
                except Exception:
                    pass
        return results

    def start_background(self):
        """Starts the server in a daemon background thread."""
        self._thread = threading.Thread(target=self.serve_forever, daemon=True)
        self._thread.start()

    def stop(self):
        """Shuts down server and waits for background thread."""
        self.shutdown()
        self.server_close()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)


class RegistryClient:
    """Client for interacting with Kale package registries."""

    def __init__(self, registry_url: Optional[str] = None, token: Optional[str] = None):
        self.registry_url = (registry_url or RegistryConfig.get_default_registry()).rstrip("/")
        self.token = token or RegistryConfig.get_token(self.registry_url)

    def _request(
        self,
        method: str,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        auth_required: bool = False,
    ) -> Dict[str, Any]:
        url = f"{self.registry_url}{path}"
        headers = {
            "Accept": "application/json",
            "User-Agent": "kale-pm/0.1.0",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        encoded_data = None
        if data is not None:
            headers["Content-Type"] = "application/json"
            encoded_data = json.dumps(data).encode("utf-8")

        req = Request(url, data=encoded_data, headers=headers, method=method)
        try:
            with urlopen(req, timeout=10) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw) if raw else {}
        except HTTPError as e:
            err_body = e.read().decode("utf-8")
            try:
                err_json = json.loads(err_body)
                msg = err_json.get("error") or err_json.get("message") or err_body
            except Exception:
                msg = err_body
            raise RuntimeError(f"HTTP {e.code}: {msg}")
        except URLError as e:
            raise ConnectionError(f"Could not connect to registry at {self.registry_url}: {e}")

    def login(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        token: Optional[str] = None,
    ) -> str:
        """Authenticates with registry and saves token locally."""
        if token:
            RegistryConfig.save_token(self.registry_url, token)
            self.token = token
            return token

        res = self._request("POST", "/api/v1/auth/login", {"username": username or "user", "password": password or ""})
        tok = res.get("token")
        if not tok:
            raise RuntimeError("Registry did not return a valid token.")
        RegistryConfig.save_token(self.registry_url, tok)
        self.token = tok
        return tok

    def publish(self, package_path_or_dir: str = ".", token: Optional[str] = None) -> Dict[str, Any]:
        """Packs (if needed) and publishes a package archive to the registry."""
        if token:
            self.token = token

        target = os.path.abspath(package_path_or_dir)
        archive_path: str
        checksum: str

        if os.path.isdir(target) or target.endswith("kale.toml"):
            proj_dir = target if os.path.isdir(target) else os.path.dirname(target)
            archive_path, checksum = pack_project(proj_dir)
            manifest = Manifest.load(os.path.join(proj_dir, "kale.toml"))
        elif target.endswith(".kale-pkg") and os.path.isfile(target):
            archive_path = target
            with open(archive_path, "rb") as f:
                checksum = hashlib.sha256(f.read()).hexdigest()

            # Read metadata from internal kale.toml
            with tarfile.open(archive_path, "r:gz") as tar:
                manifest_member = next(
                    (m for m in tar.getmembers() if m.name in ("kale.toml", "./kale.toml")),
                    None,
                )
                if not manifest_member:
                    raise RuntimeError("Archive missing kale.toml")
                f = tar.extractfile(manifest_member)
                if not f:
                    raise RuntimeError("Archive missing kale.toml content")
                if tomllib is not None:
                    manifest_data = tomllib.loads(f.read().decode("utf-8"))
                else:
                    raise RuntimeError("tomllib not available to parse TOML in archive")
                manifest = Manifest.from_dict(manifest_data)
        else:
            raise ValueError(f"Invalid package target '{package_path_or_dir}'. Must be a directory with kale.toml or a .kale-pkg file.")

        with open(archive_path, "rb") as f:
            raw_bytes = f.read()
        b64_archive = base64.b64encode(raw_bytes).decode("ascii")

        payload = {
            "name": manifest.name,
            "version": manifest.version,
            "description": manifest.description,
            "authors": manifest.authors,
            "license": manifest.license,
            "dependencies": manifest.dependencies,
            "checksum": checksum,
            "archive_base64": b64_archive,
        }

        return self._request("POST", "/api/v1/packages/publish", payload, auth_required=True)

    def search(self, query: str = "") -> List[Dict[str, Any]]:
        """Searches the registry for packages matching query."""
        from urllib.parse import quote
        q = quote(query) if query else ""
        res = self._request("GET", f"/api/v1/search?q={q}" if q else "/api/v1/packages")
        return res.get("packages", [])

    def info(self, name: str, version: Optional[str] = None) -> Dict[str, Any]:
        """Retrieves package metadata from registry."""
        if not is_safe_name(name) or (version and not is_safe_version(version)):
            raise ValueError(f"Invalid package name '{name}' or version '{version}'.")
        path = f"/api/v1/packages/{name}"
        if version:
            path = f"{path}/{version}"
        return self._request("GET", path)

    def whoami(self) -> Dict[str, Any]:
        """Checks authentication status with registry."""
        try:
            return self._request("GET", "/api/v1/auth/whoami")
        except Exception:
            return {"authenticated": False, "username": None}

    def download(self, name: str, version: str, dest_dir: str = ".") -> str:
        """Downloads a .kale-pkg archive from registry."""
        if not is_safe_name(name) or not is_safe_version(version):
            raise ValueError(f"Invalid package name '{name}' or version '{version}'.")
        url = f"{self.registry_url}/api/v1/packages/{name}/download/{version}"
        dest_dir = os.path.abspath(dest_dir)
        os.makedirs(dest_dir, exist_ok=True)
        dest_path = os.path.join(dest_dir, f"{name}-{version}.kale-pkg")

        req = Request(url, headers={"User-Agent": "kale-pm/0.1.0"})
        if self.token:
            req.add_header("Authorization", f"Bearer {self.token}")

        try:
            with urlopen(req, timeout=15) as resp, open(dest_path, "wb") as f:
                while chunk := resp.read(65536):
                    f.write(chunk)
            return dest_path
        except HTTPError as e:
            raise RuntimeError(f"Failed to download package '{name}' version '{version}': HTTP {e.code}")
        except URLError as e:
            raise ConnectionError(f"Could not connect to registry: {e}")
