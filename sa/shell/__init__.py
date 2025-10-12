"""
Shell package for SA framework.

Contains the interactive shell for the SA Query Language.
"""

from sa.shell.shell import main
from sa.shell.provider_manager import load_providers

__all__ = ["main", "load_providers"] 