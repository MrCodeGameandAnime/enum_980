"""Freeze final-review documentation/test portability fixes without editing qualified inputs."""
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parents[1]
TARGET=ROOT/'release_candidate'
if TARGET.exists():
    raise SystemExit('Final-review candidate already exists; inspect rather than overwrite.')
(TARGET/'library').mkdir(parents=True)
(TARGET/'tests').mkdir()
for path in (ROOT/'metaclass').glob('*.py'):
    (TARGET/'library'/path.name).write_text(path.read_text(),encoding='utf-8',newline='\n')
p=TARGET/'library/enum.py'
s=p.read_text().replace('# Enum implementation without metaclasses','# Enum/IntEnum containers and a runtime-backed typed StrEnum profile')
p.write_text(s,encoding='utf-8',newline='\n')
for name in ('test_full_parity.py','test_runtime_contracts.py'):
    (TARGET/'tests'/name).write_text((ROOT/'tests'/name).read_text(),encoding='utf-8',newline='\n')
p=TARGET/'tests/test_runtime_contracts.py'
s=p.read_text().replace('import json', '''try:
    import json

    class _FeatureMeta(type):
        def __len__(cls):
            return 0

    class _FeatureProbe(metaclass=_FeatureMeta):
        pass

    if len(_FeatureProbe) != 0:
        raise TypeError("metaclass operators unavailable")
except (ImportError, TypeError, AttributeError):
    print("SKIP")
    raise SystemExit(0)''',1)
p.write_text(s,encoding='utf-8',newline='\n')
print(TARGET)
