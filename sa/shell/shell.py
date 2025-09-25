#!/usr/bin/env python3
"""
Interactive shell for the SA Query Language.

This shell continuously prompts for user input and processes queries.
"""

import readline
import sys
import argparse

from sa.core.object_list import ObjectList
from sa.core.object_grouping import ObjectGrouping
from sa.query_language.execute import execute_query
from sa.query_language.render import render_object_as_group, render_object_list
from sa.shell.provider_manager import load_providers, list_providers, fetch_all_providers
from sa.query_language.chain import Chain
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


def execute_query_shell(query: str, context):
    """Execute a query string and return the result."""
    try:
        result = execute_query(query, context)
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


def load_and_fetch_data(verbose: bool = False, quiet: bool = False):
    """Load providers and fetch data, with optional verbose output and quiet mode."""
    if verbose and not quiet:
        print("🔧 Loading Providers...")
    
    providers = load_providers(quiet=quiet)
    
    if verbose and not quiet:
        print(f"📊 Loaded {len(providers)} provider(s)")
        print("🔧 Fetching Data...")
    
    all_data = fetch_all_providers(providers, quiet=quiet)
    
    if verbose and not quiet:
        print(f"📊 Loaded {len(all_data.objects)} total objects")
    
    return all_data


def run_non_interactive(query: str, verbose: bool = False, quiet: bool = False, debug: bool = False, profiling: bool = False):
    """Run a single query in non-interactive mode."""
    all_data = load_and_fetch_data(verbose, quiet)
    
    # Set debug mode globally if requested
    if debug:
        import sa.query_language.operators
        sa.query_language.operators.DEBUG_ENABLED = True
    
    # Set profiling mode globally if requested
    if profiling:
        import sa.query_language.operators
        sa.query_language.operators.PROFILING_ENABLED = True
    
    result, error = execute_query_shell(query, all_data)
    
    if error:
        print(f"Error: {error}")
    else:
        print(format_result(result))


def main():
    """Main entry point that handles both interactive and non-interactive modes."""
    parser = argparse.ArgumentParser(
        description="SA Query Language Shell",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    # Start interactive shell
  %(prog)s ".equals(.get_field('name'), 'John')"  # Run single query
  %(prog)s -q ".get_field('department')"     # Run query quietly
  %(prog)s -v ".filter(.equals(.get_field('salary'), 75000))"  # Run query with verbose output
  %(prog)s --debug ".equals(.get_field('name'), 'John')"  # Run query with debug output
  %(prog)s --print-profiling-information ".equals(.get_field('name'), 'John')"  # Run query with profiling output
  %(prog)s --update                          # Run ~/.sa/sa-installer and exit
        """
    )
    parser.add_argument(
        'query', 
        nargs='?', 
        help='Query to execute (if not provided, starts interactive shell)'
    )
    parser.add_argument(
        '-v', '--verbose', 
        action='store_true', 
        help='Enable verbose output for non-interactive mode'
    )
    parser.add_argument(
        '-q', '--quiet', 
        action='store_true', 
        help='Suppress provider loading messages in non-interactive mode'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug output for operators'
    )
    parser.add_argument(
        '--print-profiling-information',
        action='store_true',
        help='Print timing information for each operation in the query'
    )
    parser.add_argument(
        '--update',
        action='store_true',
        help='Run ~/.sa/sa-installer and exit'
    )
    
    args = parser.parse_args()
    
    # Handle update command
    if args.update:
        import subprocess
        import os
        installer_path = os.path.expanduser("~/.sa/sa-installer")
        if os.path.exists(installer_path):
            print("🔄 Running sa-installer...")
            subprocess.run([installer_path], check=True)
            print("✅ Update completed successfully!")
        else:
            print(f"❌ Error: Installer not found at {installer_path}")
            sys.exit(1)
        return
    
    # If a query is provided, run in non-interactive mode
    if args.query:
        verbose = args.verbose and not args.quiet
        run_non_interactive(args.query, verbose, args.quiet, args.debug, args.print_profiling_information)
        return
    
    # Otherwise, start interactive shell
    run_interactive_shell(args.debug, args.print_profiling_information)


def run_interactive_shell(debug: bool = False, profiling: bool = False):
    """Run the interactive shell loop."""
    print_header()
    
    # Load providers at startup
    print_section_header("Loading Providers")
    providers = load_providers()
    print(f"\n📊 Summary: {len(providers)} provider(s) loaded")
    print_section_footer()
    
    # Fetch data from all providers that support ALL_AT_ONCE mode
    print_section_header("Fetching Data")
    all_data = fetch_all_providers(providers)
    print(f"\n📊 Summary: {len(all_data.objects)} total objects loaded")
    print_section_footer()
    
    # Set debug mode if requested
    if debug:
        import sa.query_language.operators
        sa.query_language.operators.DEBUG_ENABLED = True
        print("🐛 Debug mode enabled")
        print()
    
    # Set profiling mode if requested
    if profiling:
        import sa.query_language.operators
        sa.query_language.operators.PROFILING_ENABLED = True
        print("⏱️  Profiling mode enabled")
        print()
    
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
                print("  debug    - Toggle debug mode on/off")
                print("  profile  - Toggle profiling mode on/off")
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
                all_data = fetch_all_providers(providers)
                print(f"\n📊 Summary: {len(all_data.objects)} total objects loaded")
                print_section_footer()
                print("✅ Data refreshed successfully!")
                print()
                continue
            
            # Check for debug command
            if user_input.lower() == 'debug':
                import sa.query_language.operators
                sa.query_language.operators.DEBUG_ENABLED = not sa.query_language.operators.DEBUG_ENABLED
                status = "enabled" if sa.query_language.operators.DEBUG_ENABLED else "disabled"
                print(f"\n🐛 Debug mode {status}")
                print()
                continue
            
            # Check for profile command
            if user_input.lower() == 'profile':
                import sa.query_language.operators
                sa.query_language.operators.PROFILING_ENABLED = not sa.query_language.operators.PROFILING_ENABLED
                status = "enabled" if sa.query_language.operators.PROFILING_ENABLED else "disabled"
                print(f"\n⏱️  Profiling mode {status}")
                print()
                continue
            
            # Skip empty input
            if not user_input:
                continue
            
            # Execute the query
            result, error = execute_query_shell(user_input, all_data)
            
            if error:
                print(f"❌ Error: {error}")
            else:
                print(format_result(result, show_count=False))

            print()

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except EOFError:
            print("\n\n👋 Goodbye!")
            break


if __name__ == "__main__":
    main()
