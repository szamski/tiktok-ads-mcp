import asyncio
import sys
from .server import main as run_server # Import the main function from server.py

def cli():
    """
    This is the command-line entry point defined in pyproject.toml.
    It simply calls the main async function from the server module.
    """
    print("Starting TikTok Ads MCP via CLI entry point...")
    try:
        # Check if an event loop is running, which is common in some environments
        if sys.version_info >= (3, 7):
            asyncio.run(run_server())
        else:
            # Fallback for older python versions if necessary
            loop = asyncio.get_event_loop()
            loop.run_until_complete(run_server())
    except KeyboardInterrupt:
        print("\nServer shut down by user.")
        sys.exit(0)

if __name__ == "__main__":
    cli()