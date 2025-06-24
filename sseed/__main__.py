"""Main entry point when running sseed as a module with python -m sseed."""

import sys

from sseed.cli.main import main

if __name__ == "__main__":
    sys.exit(main())
