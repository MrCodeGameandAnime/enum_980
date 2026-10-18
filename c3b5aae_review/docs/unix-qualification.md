# Real Unix qualification

## Result

Actual Linux x86-64 Unix standard ports were built from both pinned MicroPython
sources, stock and patched. The final candidate passed its targeted matrix and
DD comparison corpus on both patched runtimes, normally and with optimization.
The upstream basics/JSON suites passed on stock and patched runtimes with
identical skip sets. This qualifies the tested subset, not all metaclass behavior:
see the open lifecycle finding in [the final review](final-review.md).

| Runtime | Source pin | Upstream tests passed per build | Individual cases per build | Skips |
| --- | --- | ---: | ---: | ---: |
| 1.29.0 | `0fd6c573ea815774668bbb16b8e197c8822368b2` | 560 | 17,484 | 29 |
| 1.30.0-preview | `9a3a0c0d5ea946a4a1b6ff0e3f3087c8adbcac01` | 562 | 17,506 | 29 |

Counts apply separately to stock and patched builds. Neither comparison has new
failures or changed skip sets. Unix enables more standard-port features than the
previous Windows build, which explains the different counts.

For each version, 33 targeted commands cover native CPython reference behavior,
forced library behavior on CPython, patched MicroPython, normal/optimized modes,
the optional-feature stock skip, and both corpus runs. All 11 DD requirement
groups match over the unchanged corpus of 61 observations. Original package
suites execute their 13 enum and 7 mini tests on MicroPython. Qualification
requires exact output counts for the new JSON-reporting checks and explicitly
checks unittest output as well as process status.

## Environment

- Linux x86-64, Docker Desktop Linux engine.
- CPython **3.12.15**, GCC **12.2.0**, GNU Make **4.3**, Git **2.39.5**.
- Base image: `python@sha256:34386ef0cb081344d7ec1c103ba398e6e9f64e9ab3a1509accc92a4e24a07258`.
- Built image ID: `sha256:83367fc61bdbb483b22243d3cefd760ea33eac02b8d75d9ee1a5cb37ce6a1261`.
- Unix standard variant with its default frozen manifest, matching the package
  CI's port family. Both builds use `CFLAGS_EXTRA=-O0`; patched builds additionally
  enable the four metaclass feature flags listed in the candidate README.
- Core source Git pins and each dependency submodule are checked out directly.
  Both use micropython-lib `ee4bb8ff139e24c42b739935fbd8ec7c4d061e02` for the
  port's frozen standard-library dependencies.

The read-only project mount supplies reviewed inputs. A dedicated Docker Linux
volume (`enum980-unix-review-work`) holds build trees and binaries. Results are
saved to the project's review results directory. The earlier Windows-mounted
source-copy attempt was stopped and is explicitly marked incomplete.

## Evidence

- [Completed run, exact commands, runtime identities, binary and input hashes](../root/results/unix/run-20261018T181738Z/qualification.json)
- [Final input/patch checks, Unix versus Windows source fidelity, README runs and inherited-defect reproduction](../root/results/unix/run-20261018T181738Z/final-review-checks.json)
- [Compiler and toolchain versions](../root/results/unix/run-20261018T181738Z/toolchain.stdout.txt)
- [Revised patch application checks on both core pins and the library pin](../root/release_candidate/patches/application-check.json)
- [Previous 1.29.0 inputs and full preview archive preservation](../root/results/runtime-130-profile/input-integrity.json)

The patched Unix trees match all eight changed core sources in the previously
qualified Windows trees after newline normalization. No additional core source
changes were needed for Linux. The final library revision adds documentation,
comment/newline cleanup and a guarded optional-feature test; enum behavior stays
identical to the preceding qualified profile.

## Repeat

[Dockerfile](../root/config/unix/Dockerfile),
[qualification runner](../root/src/qualify_unix.py), and
[final cross-check runner](../root/src/verify_unix_review.py) are saved locally.
The runner writes a timestamped result directory and only creates `current.json`
after both versions finish. It records incomplete runs separately when it catches
an error. Use a fresh Linux volume for a complete rebuild; the existing volume is
retained as evidence. Mount the project read-only at `/project`, that volume at
`/work`, and `c3b5aae_review/root/results/unix` at `/results`.

Build the image from the saved Dockerfile, then run these inside that configured
container:

```sh
python -B /project/c3b5aae_review/root/src/qualify_unix.py
python -B /project/c3b5aae_review/root/src/verify_unix_review.py
```

The first command fetches pinned public sources, builds stock/patched interpreters
and mpy-cross, executes the matrix and compares upstream suites. The second checks
saved hashes, source fidelity, README examples and the outstanding hook-order
finding. No publication action is part of either command.
