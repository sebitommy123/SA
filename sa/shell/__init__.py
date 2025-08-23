"""
Shell package for SA framework.

Contains the interactive shell for the SA Query Language.
"""

from .shell import main
from .provider_manager import load_providers, get_provider_count, list_providers, fetch_all_providers

__all__ = ["main", "load_providers", "get_provider_count", "list_providers", "fetch_all_providers"] 