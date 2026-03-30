"""
HiveRecon - AI-Powered Reconnaissance Framework

Main entry point for the application.
"""

import asyncio
import sys

from hiverecon.cli import app


def main():
    """Main entry point."""
    try:
        app()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Exiting...")
        sys.exit(130)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
