"""
SA - Semantic Analysis Framework

A Python framework for working with semantic objects and query languages.
"""

__version__ = "0.1.0"
__author__ = "Sebi"
__description__ = "Semantic Analysis Framework for generic JSON objects"

from sa.core.sa_object import SAObject
from sa.core.object_list import ObjectList
from sa.shell.shell import main as shell_main

__all__ = ["SAObject", "ObjectList", "shell_main"] 