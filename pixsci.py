#!/usr/bin/env python3
# pixsci: pixel-art science explainers from a plan. Commands: pixel_kit/cli.py, or `pixsci.py --help`.
#   .venv/bin/python pixsci.py <command> ... [--json]
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pixel_kit.cli import main

if __name__ == "__main__":
    sys.exit(main())
