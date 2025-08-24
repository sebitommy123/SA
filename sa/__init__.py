"""
SA - Semantic Analysis Framework

A Python framework for working with semantic objects and query languages.
"""

__version__ = "0.1.0"
__author__ = "Sebi"
__description__ = "Semantic Analysis Framework for generic JSON objects"

from .core.sa_object import SAObject
from .query_language.object_list import ObjectList

__all__ = ["SAObject", "ObjectList"] 