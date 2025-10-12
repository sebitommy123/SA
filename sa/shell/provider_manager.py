"""
Provider management for the SA Query Language Shell.

Handles loading and managing provider endpoint connections.
"""

import os
import json
import requests
from typing import List, Optional, Union
from dataclasses import dataclass

from sa.core.object_grouping import ObjectGrouping, group_objects
from sa.core.sa_object import SAObject
from sa.core.object_list import ObjectList
from sa.core.scope import Scope
from sa.query_language.query_scope import QueryScope, Scopes


@dataclass
class ProviderConnection:
    """Represents a connection to a provider endpoint."""
    url: str
    name: str = ""
    lazy_loading_scopes: List[Scope] = None
    
    def load(self, quiet: bool = False) -> bool:
        try:
            # Ensure URL ends with /hello
            hello_url = self.url.rstrip('/') + '/hello'
            
            # Make GET request to /hello endpoint
            response = requests.get(hello_url, timeout=10)
            response.raise_for_status()
            
            # Parse JSON response
            data = response.json()
            
            # Extract name and lazy loading scopes
            self.name = data.get('name', 'Unknown')
            
            # Convert lazy loading scopes from JSON to Scope objects
            lazy_scopes_data = data.get('lazy_loading_scopes', [])
            self.lazy_loading_scopes = []
            for scope_data in lazy_scopes_data:
                if isinstance(scope_data, dict) and 'type' in scope_data:
                    scope = Scope(
                        type=scope_data['type'],
                        fields=scope_data.get('fields', '*')
                    )
                    self.lazy_loading_scopes.append(scope)
            
            if not quiet:
                print(f"  ✓ Connected to: {self.name}")
                print(f"    URL:  {self.url}")
                
                # Log lazy loading scopes (only types, not fields)
                if self.lazy_loading_scopes:
                    scope_types = [scope.type for scope in self.lazy_loading_scopes]
                    print(f"    Lazy loading supported for types: {', '.join(scope_types)}")
                else:
                    print(f"    No lazy loading scopes available")
            return True
            
        except requests.exceptions.RequestException as e:
            if not quiet:
                print(f"  ✗ Failed to connect to {self.url}: {e}")
            return False
        except json.JSONDecodeError as e:
            if not quiet:
                print(f"  ✗ Invalid JSON response from {self.url}: {e}")
            return False
        except Exception as e:
            if not quiet:
                print(f"  ✗ Unexpected error connecting to {self.url}: {e}")
            return False

    def fetch_initial_data(self, quiet: bool = False) -> list[ObjectGrouping]:
        try:
            # Make GET request to /all_data endpoint
            all_data_url = self.url.rstrip('/') + '/all_data'
            response = requests.get(all_data_url, timeout=30)
            response.raise_for_status()
            
            # Parse JSON response
            data = response.json()
            
            # Convert each object to SAObject
            sa_objects = []
            for obj_data in data:
                try:
                    sa_obj = SAObject(obj_data)
                    sa_objects.append(sa_obj)
                except Exception as e:
                    if not quiet:
                        print(f"    ⚠ Warning: Failed to create SAObject: {e}")
                    continue
            
            if not quiet:
                print(f"    ✓ Fetched {len(sa_objects)} objects")
            return sa_objects
            
        except requests.exceptions.RequestException as e:
            if not quiet:
                print(f"    ✗ Failed to fetch data: {e}")
            return None
        except json.JSONDecodeError as e:
            if not quiet:
                print(f"    ✗ Invalid JSON response: {e}")
            return None
        except Exception as e:
            raise e

@dataclass
class Providers:
    connections: List[ProviderConnection]
    all_data: ObjectList

    def fetch_initial_data(self, quiet: bool = False) -> ObjectList:
        all_objects = []
        
        for connection in self.connections:
            if not quiet:
                print(f"  📥 Fetching from: {connection.name}")
            data = connection.fetch_initial_data(quiet=quiet)
            all_objects.extend(data)
        
        self.all_data = ObjectList(group_objects(all_objects))

    def print(self) -> None:
        if not self.connections:
            print("No providers loaded.")
            return
        
        print(f"📋 Loaded {len(self.connections)} provider(s):")
        for i, connection in enumerate(self.connections, 1):
            print(f"  {i}. {connection.name}")
            print(f"     URL:  {connection.url}")
            if connection.lazy_loading_scopes:
                scope_types = [scope.type for scope in connection.lazy_loading_scopes]
                print(f"     Lazy loading: {', '.join(scope_types)}")
            print()
    
    @property
    def all_scopes(self) -> list[Scope]:
        return Scope.union(
            [scope for connection in self.connections for scope in connection.lazy_loading_scopes]
        )


def load_providers(providers_file: Union[str, None] = None, quiet: bool = False) -> Providers:
    """
    Load provider URLs from a text file and create ProviderConnection objects.
    
    Args:
        providers_file: Path to the providers file (defaults to ~/.sa/saps.txt)
        quiet: If True, suppress output messages
        
    Returns:
        List of ProviderConnection objects
    """
    connections = []
    
    # Default to ~/.sa/saps.txt if no file specified
    if providers_file is None:
        home_dir = os.path.expanduser("~")
        sa_dir = os.path.join(home_dir, ".sa")
        providers_file = os.path.join(sa_dir, "saps.txt")
        
        # Create .sa directory if it doesn't exist
        if not os.path.exists(sa_dir):
            os.makedirs(sa_dir, exist_ok=True)
            
        # Create default saps.txt if it doesn't exist
        if not os.path.exists(providers_file):
            with open(providers_file, 'w') as f:
                f.write("# SA Provider endpoints\n")
                f.write("# Add your provider URLs here, one per line\n")
                f.write("# Lines starting with # are comments\n")
                f.write("# Example:\n")
                f.write("# https://api.example.com\n")
                f.write("# http://localhost:8080\n")
    
    if not os.path.exists(providers_file):
        if not quiet:
            print(f"⚠ Warning: {providers_file} not found. No providers loaded.")
        return connections
    
    try:
        with open(providers_file, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                # Skip empty lines and comments
                if line and not line.startswith('#'):
                    # Create connection and load provider info
                    connection = ProviderConnection(url=line)
                    if connection.load(quiet):
                        connections.append(connection)
                    else:
                        if not quiet:
                            print(f"  ✗ Failed to load provider: {line}")
    except Exception as e:
        if not quiet:
            print(f"✗ Error reading {providers_file}: {e}")
    
    return Providers(
        connections=connections,
        all_data=ObjectList([])
    )