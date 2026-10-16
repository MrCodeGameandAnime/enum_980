# Enum upstream investigation

A local, DD-derived comparison of CPython's StrEnum, DD's original overlay, and [micropython-lib PR #980](https://github.com/micropython/micropython-lib/pull/980) by [@IhorNehrutsa](https://github.com/IhorNehrutsa). This project is an investigation, not a published enum library.

- [Background](background.md)
- [Requirements and source references](requirements.md)
- [Source census and original file hashes](dd-enum-census.json)
- [Measured three-way comparison](comparison.md)
- [Raw machine-readable results](three-way-results.json)
- [Findings and maintainer questions](findings.md)
- [PR #1061 with its proposed core: separate results](pr1061-comparison.md)
- [PR #1061 runtime/package sources](pr1061-results.json)

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

## PR #1061 experimental runtime

This separate experiment builds the pinned companion core on Windows. It requires
CPython 3.12 and Visual Studio Build Tools with MSBuild and the v145 C++ toolset
(Win32). The measured build used MSVC 19.51. Run from the project directory:

```powershell
python root/src/prepare_pr1061.py
./root/src/build-pr1061.ps1 -Python 'C:/path/to/python.exe' -MSBuild 'C:/path/to/MSBuild.exe'
python root/src/check_pr1061.py
```

Use your CPython 3.12 executable in place of `python` if it is not the PATH default.
Preparation downloads two pinned GitHub archives, verifies their SHA256 hashes,
extracts them under `root/build/pr1061/`, and creates the source records there.
For an offline rebuild, add `--archive-dir <cache-directory>` to preparation; the
cache must contain `core.tar.gz` and `library.tar.gz` matching the pinned hashes.
Existing extracted source files are verified against the archives on every run;
modified or incomplete trees fail instead of being silently reused.

The check regenerates and validates all four metaclass feature probes, then runs
the unchanged corpus and both controls. It uses the committed stock-runtime
baseline; no earlier local logs, reference files or generated metadata are needed.
Reports go to `docs/`, and build outputs and logs stay in ignored `root/build/`
and `root/results/`. This verifies the focused corpus, not the full upstream suite
or embedded-board support.

## Continuous integration

[GitHub Actions](../.github/workflows/ci.yml) runs on pushes, pull requests and
manual dispatches, using CPython 3.12 on the Windows Server 2025 / Visual Studio
2026 runner. It builds the pinned stock MicroPython 1.29.0 Windows port, runs the
harness tests with MicroPython integration enabled, and executes the three-way
comparison. It then downloads and verifies the pinned #1061/core archives, builds
the experimental interpreter, checks all four metaclass features and runs that
comparison with both controls.

Stock builds disable frozen modules via `root/config/stock.props`; the comparisons
load the included candidate modules from source. The experimental build keeps its
existing `root/config/pr1061.props` configuration. Both builds use Release/Win32
and the v145 C++ toolset. Action versions and the stock source commit are pinned.

Reports and execution/build logs are retained as workflow artifacts for 14 days,
including available logs when a step fails. CI does not update the published
measurements or post upstream. Expected candidate differences appear in reports;
build, test, protocol and feature-probe failures fail the job. The first hosted
run starts after the workflow is pushed to GitHub.
