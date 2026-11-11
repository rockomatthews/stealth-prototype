"""Run current specialty takedown checks (replaces obsolete kick finisher)."""
import runpy
from pathlib import Path
runpy.run_path(str(Path(__file__).with_name('run_specialty_acceptance.py')),run_name='__main__')
