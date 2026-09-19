"""Kale Package Manager (pm) module.

Provides project configuration (kale.toml), project bootstrapping (new/init),
packaging (.kale-pkg), dependency management (add/remove), and publishing
registry integration.
"""

from .manifest import Manifest, find_manifest
from .project import create_project, init_project
from .pack import pack_project
from .registry import RegistryClient, RegistryServer

__all__ = [
    "Manifest",
    "find_manifest",
    "create_project",
    "init_project",
    "pack_project",
    "RegistryClient",
    "RegistryServer",
]
