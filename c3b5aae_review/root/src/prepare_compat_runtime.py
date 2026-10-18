"""Current entry point: the reviewed MicroPython 1.29.0 port."""

from pathlib import Path
import runpy

runpy.run_path(str(Path(__file__).with_name("prepare_runtime_129.py")), run_name="__main__")
