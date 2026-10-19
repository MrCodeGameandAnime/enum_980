# Enum upstream investigation

A local, DD-derived comparison of CPython's StrEnum, DD's original overlay, and [micropython-lib PR #980](https://github.com/micropython/micropython-lib/pull/980) by [@IhorNehrutsa](https://github.com/IhorNehrutsa). This project is an investigation, not a published enum library.

- [Background](background.md)
- [Requirements and source references](requirements.md)
- [Source census and original file hashes](dd-enum-census.json)
- [Measured three-way comparison](comparison.md)
- [Raw machine-readable results](three-way-results.json)
- [Findings and maintainer questions](findings.md)

## Layout

- `docs/`: requirements, findings and measured results.
- `root/src/cases.py`: the same synthetic observations for all three implementations.
- `root/src/compare.py`: source validation, execution and report generation.
- `root/src/prepare_sources.py`: copies only DD enum.py and fetches the pinned PR enum.py.
- `root/tests/`: runner integrity and regression tests.
- `root/vendor/`: byte-preserved source snapshots with source records.
- `root/results/`: ignored execution logs.

DD's code remains unchanged. Copied candidate implementations retain their original
behavior; the comparison does not patch them to improve outcomes. No game models
are imported by the runtime cases. Historical research is summarized in [Background](background.md); the local reference files are not distributed or needed to reproduce the measurements.

## Run

Use CPython 3.12. From this project directory:

```sh
python root/src/compare.py --micropython <MicroPython-1.29.0-executable>
python -B -m unittest discover -s root/tests -v
```

The committed source snapshots allow this comparison to run offline without a DD checkout.
To refresh them from the original sources, optionally run
`python root/src/prepare_sources.py --dd-root <DD-repository>`; this needs internet access for the pinned PR file. Set `MICROPYTHON_EXECUTABLE` for the
runner's MicroPython integration test; otherwise that one test skips.

The local executable used for this report is:

```text
C:/Users/User/AppData/Local/DungeonDrifters/micropython/v1.29.0/source/ports/windows/build-standard/ReleaseWin32/micropython.exe
```

Compare both interpreter names, versions and platforms before combining results
from different machines or ports. Runtime controls are retained in the report.
Upstream posting or implementation changes require a separate decision.

## Continuous integration

[GitHub Actions](../.github/workflows/ci.yml) runs on pushes, pull requests and
manual dispatches using CPython 3.12 on the Windows Server 2025 / Visual Studio
2026 runner. It builds unmodified, pinned MicroPython 1.29.0, runs the harness
tests with MicroPython integration enabled, and executes the three-way comparison.

Stock builds disable frozen modules via `root/config/stock.props`; comparisons
load the included candidate modules from source. The build uses Release/Win32
and the v145 C++ toolset. Action versions and the stock source commit are pinned.

Reports and logs are retained as workflow artifacts for 14 days. CI does not
update the published measurements or post upstream. Expected candidate differences
appear in reports; build, test and protocol failures fail the job.
