"""
Provider management for the SA Query Language Shell.

Handles loading and managing provider endpoint connections.
"""

import os
import json
import requests
from typing import List, Optional, Union
from dataclasses import dataclass
from sa.core.sa_object import SAObject
from sa.query_language.object_list import ObjectList


@dataclass
class ProviderConnection:
    """Represents a connection to a provider endpoint."""
    url: str
    name: str = ""
    mode: str = ""
    
    def load(self, quiet: bool = False) -> bool:
        """
        Load provider information by calling the /hello endpoint.
        
        Args:
            quiet: If True, suppress output messages
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure URL ends with /hello
            hello_url = self.url.rstrip('/') + '/hello'
            
            # Make GET request to /hello endpoint
            response = requests.get(hello_url, timeout=10)
            response.raise_for_status()
            
            # Parse JSON response
            data = response.json()
            
            # Extract name and mode
            self.name = data.get('name', 'Unknown')
            self.mode = data.get('mode', 'Unknown')
            
            if not quiet:
                print(f"  ✓ Connected to: {self.name}")
                print(f"    Mode: {self.mode}")
                print(f"    URL:  {self.url}")
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
    
    def fetch(self, quiet: bool = False) -> Optional[ObjectList]:
        """
        Fetch data from the provider if mode is "ALL_AT_ONCE".
        
        Args:
            quiet: If True, suppress output messages
            
        Returns:
            ObjectList of SAObjects if successful, None otherwise
        """
        if self.mode != "ALL_AT_ONCE":
            return None
        
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
            return ObjectList(sa_objects)
            
        except requests.exceptions.RequestException as e:
            if not quiet:
                print(f"    ✗ Failed to fetch data: {e}")
            return None
        except json.JSONDecodeError as e:
            if not quiet:
                print(f"    ✗ Invalid JSON response: {e}")
            return None
        except Exception as e:
            if not quiet:
                print(f"    ✗ Unexpected error: {e}")
            return None


def load_providers(providers_file: Union[str, None] = None, quiet: bool = False) -> List[ProviderConnection]:
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
    
    return connections


def fetch_all_providers(connections: List[ProviderConnection], quiet: bool = False) -> ObjectList:
    """
    Fetch data from all providers that support ALL_AT_ONCE mode.
    
    Args:
        connections: List of ProviderConnection objects
        quiet: If True, suppress output messages
        
    Returns:
        Single ObjectList containing all objects from all providers
    """
    all_objects = []
    
    for connection in connections:
        if connection.mode == "ALL_AT_ONCE":
            if not quiet:
                print(f"  📥 Fetching from: {connection.name}")
            data = connection.fetch(quiet=quiet)
            if data:
                # Extend the list with objects from this provider
                all_objects.extend(data.objects)
    
    return ObjectList(all_objects)


def get_provider_count(connections: List[ProviderConnection]) -> int:
    """
    Get the count of loaded provider connections.
    
    Args:
        connections: List of ProviderConnection objects
        
    Returns:
        Number of provider connections
    """
    return len(connections)


def list_providers(connections: List[ProviderConnection]) -> None:
    """
    List all loaded provider connections.
    
    Args:
        connections: List of ProviderConnection objects
    """
    if not connections:
        print("No providers loaded.")
        return
    
    print(f"📋 Loaded {len(connections)} provider(s):")
    for i, connection in enumerate(connections, 1):
        print(f"  {i}. {connection.name}")
        print(f"     Mode: {connection.mode}")
        print(f"     URL:  {connection.url}")
        print() 