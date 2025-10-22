#!/usr/bin/env python3
"""
Interactive shell for the SA Query Language.

This shell continuously prompts for user input and processes queries.
"""

import readline
import sys
import argparse

from sa.query_language.errors import QueryError
from sa.query_language.scopes import Scopes
from sa.query_language.query_state import QueryState
from sa.query_language.parser import execute_query, execute_query_fully
from sa.core.object_list import ObjectList
from sa.core.object_grouping import ObjectGrouping
from sa.query_language.render import render_object_as_group, render_object_list
from sa.shell.provider_manager import Providers, load_providers
from sa.query_language.chain import Chain
from sa.query_language.debug import debugger
import traceback

VERSION = 22

def print_header():
    """Print the shell header with nice formatting."""
    print("╔══════════════════════════════════════════════════════════════╗")
    print(f"║                    SA Query Language Shell v{VERSION}                 ║")
    print("║                                                              ║")
    print("║  Type 'quit', 'exit', or 'q' to exit                        ║")
    print("║  Type 'help' for available commands                         ║")
    print("║  Type queries like: .equals(.get_field('name'),'John')      ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()


def print_section_header(title: str):
    """Print a section header with consistent formatting."""
    print(f"🔧 {title}")
    print("─" * (len(title) + 4))


def print_section_footer():
    """Print a section footer separator."""
    print("─" * 60)
    print()


def execute_query_shell(query: str, providers: Providers):
    """Execute a query string and return the result."""
    try:
        result = execute_query_fully(query, providers)
        return result, None
    except Exception as e:
        return None, traceback.format_exc()


def format_result(result, show_count: bool = True):
    """Format a query result for display."""
    if isinstance(result, ObjectList):
        # It's an ObjectList
        if len(result.objects) == 0:
            return "No objects found"
        else:
            output = f"Found {len(result.objects)} object(s):\n" if show_count else ""
            output += render_object_list(result)
            return output
    elif isinstance(result, ObjectGrouping):
        return render_object_as_group(result)
    elif isinstance(result, bool):
        return str(result)
    elif isinstance(result, (list, tuple)):
        return str(result)
    else:
        return str(result)


def run_non_interactive(query: str, raise_errors: bool = False, debug_file: str = None):
    """Run a single query in non-interactive mode."""
    providers = load_providers()
    providers.fetch_initial_data()

    print("-" * 100)
    
    result, error = execute_query_shell(query, providers)

    if isinstance(result, QueryError):
        if raise_errors:
            raise result

    if error:
        print(f"Error: {error}")
    else:
        print(format_result(result))
    
    if debug_file:
        print(f"🐛 Saving debug output to: {debug_file}")
        html_content = debugger.to_html()
        with open(debug_file, 'w') as f:
            f.write(html_content)
        print(f"\n🐛 Debug output saved to: {debug_file}")


def main():
    """Main entry point that handles both interactive and non-interactive modes."""
    parser = argparse.ArgumentParser(
        description="SA Query Language Shell",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    # Start interactive shell
  %(prog)s ".equals(.get_field('name'), 'John')"  # Run single query
  %(prog)s --print-profiling-information ".equals(.get_field('name'), 'John')"  # Run query with profiling output
  %(prog)s --debug result.html ".equals(.get_field('name'), 'John')"  # Run query with debug output to HTML file
  %(prog)s --raise ".equals(.get_field(\\'name\\'), \\'John\\')"  # Run query and raise QueryError exceptions
  %(prog)s --update                          # Update SA to latest version from GitHub
        """
    )
    parser.add_argument(
        'query', 
        nargs='?', 
        help='Query to execute (if not provided, starts interactive shell)'
    )
    parser.add_argument(
        '--print-profiling-information',
        action='store_true',
        help='Print timing information for each operation in the query'
    )
    parser.add_argument(
        '--update',
        action='store_true',
        help='Update SA to the latest version from GitHub'
    )
    parser.add_argument(
        '--raise',
        dest='raise_errors',
        action='store_true',
        help='Raise QueryError exceptions instead of printing them'
    )
    parser.add_argument(
        '--debug',
        metavar='FILE',
        help='Save debug output to HTML file (e.g., --debug result.html)'
    )
    
    args = parser.parse_args()
    
    # Handle update command
    if args.update:
        import subprocess
        import sys
        
        print("🔄 Updating SA to the latest version from GitHub...")
        print("📦 Running: pip install --upgrade git+https://github.com/sebitommy123/SA.git")
        
        try:
            # Run pip install to update from GitHub
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", "--upgrade", 
                "git+https://github.com/sebitommy123/SA.git"
            ], check=True, capture_output=True, text=True)
            
            print("✅ Update completed successfully!")
            print("🚀 You can now use the latest version of SA")
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Error updating SA: {e}")
            if e.stdout:
                print(f"stdout: {e.stdout}")
            if e.stderr:
                print(f"stderr: {e.stderr}")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Unexpected error during update: {e}")
            sys.exit(1)
        
        return
    
    # If a query is provided, run in non-interactive mode
    if args.query:
        run_non_interactive(args.query, args.raise_errors, args.debug)
        return
    
    # Otherwise, start interactive shell
    run_interactive_shell(args.debug)


def run_interactive_shell(debug_file: str = None):
    """Run the interactive shell loop."""
    print_header()
    
    # Load providers at startup
    print_section_header("Loading Providers")
    providers = load_providers()
    print(f"\n📊 Summary: {len(providers.connections)} provider(s) loaded")
    print_section_footer()

    # Fetch data from all providers that support ALL_AT_ONCE mode
    print_section_header("Fetching Data")
    providers.fetch_initial_data()
    print(f"\n📊 Summary: {len(providers.all_data._objects)} total objects loaded")
    print_section_footer()
    
    # Main shell loop
    print("🚀 Ready for queries! Type your commands below:")
    print("💡 Example: employee[.skills.includes('Recruitment')].count()")
    print()
    
    while True:
        try:
            # Get user input
            user_input = input("sa> ").strip()
            
            # Check for exit commands
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!")
                break
            
            # Check for help command
            if user_input.lower() == 'help':
                print("\n📖 Available Commands:")
                print("  help     - Show this help message")
                print("  refresh  - Reload data from all providers")
                print("  quit     - Exit the shell")
                print("  exit     - Exit the shell")
                print("  q        - Exit the shell")
                print()
                print("📝 Query Examples:")
                print("  .get_field('name')                    - Get all name values")
                print("  .equals(.get_field('name'), 'John')   - Find objects with name='John'")
                print("  .filter(.equals(.get_field('department'), 'Engineering'))")
                print("                                        - Filter by department")
                print()
                continue
            
            # Check for refresh command
            if user_input.lower() == 'refresh':
                print("\n🔄 Refreshing data from all providers...")
                print_section_header("Refreshing Data")
                providers.fetch_initial_data()
                print(f"\n📊 Summary: {len(providers.all_data.objects)} total objects loaded")
                print_section_footer()
                print("✅ Data refreshed successfully!")
                print()
                continue
            
            
            # Skip empty input
            if not user_input:
                continue
            
            # Execute the query
            result, error = execute_query_shell(user_input, providers)
            
            if error:
                print(f"❌ Error: {error}")
            else:
                print(format_result(result, show_count=False))
            
            if debug_file:
                print(f"🐛 Saving debug output to: {debug_file}")
                html_content = debugger.to_html()
                with open(debug_file, 'w') as f:
                    f.write(html_content)
                print(f"\n🐛 Debug output saved to: {debug_file}")

            print()

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except EOFError:
            print("\n\n👋 Goodbye!")
            break


if __name__ == "__main__":
    main()
