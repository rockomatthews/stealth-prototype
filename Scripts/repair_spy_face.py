"""Regenerate only derived spy face/goggles, preserving source characters."""
from pathlib import Path
p=Path(__file__).resolve().parent/'prepare_equipment.py'
s=p.read_text();exec(compile(s[:s.index('# Author a shoulder reach')],str(p),'exec'),{'__file__':str(p),'__name__':'__main__'})
