# Additional qualification: MicroPython 1.30.0-preview

## Result

The existing runtime/library patch series qualifies unchanged against upstream
MicroPython **1.30.0-preview**, pinned at
[`9a3a0c0d5ea946a4a1b6ff0e3f3087c8adbcac01`](https://github.com/micropython/micropython/commit/9a3a0c0d5ea946a4a1b6ff0e3f3087c8adbcac01).
This was the default-branch head selected at the start of the run. Results apply
to that exact snapshot, not every future preview commit.

The 1.29.0 base, patches, binaries, tooling and qualification inputs remain intact.
This adds a second qualified runtime target; it does not replace the 1.29.0 base.

## Evidence

| Check | Result |
| --- | --- |
| Complete patch series | All six patches apply unchanged; byte-identical to the 1.29.0 series |
| Targeted matrix | 33 commands pass on CPython 3.12.14 and patched preview, normal/optimized |
| DD corpus | All 11 requirement groups pass over the unchanged 61 observations |
| Upstream basics/JSON tests | 551 pass on stock preview and 551 on patched preview |
| Individual upstream cases | 17,425 per runtime |
| Skips | Identical 40-test skip sets |
| New failures | None |
| Source fidelity | All 6,823 archived source files checked; only the intended eight files change |
| 1.29.0 preservation | Every input in the existing 1.29.0 qualification still matches its hash |
| Lint | Ruff 0.11.6 passes with the pinned library configuration |

The targeted matrix covers runtime metaclass operations, real typed enum members,
class length/subscription, selective mutation protection, public metadata,
representation, JSON values and keys, factories, hook composition, fresh imports,
both module orders, and the existing 13 enum plus 7 mini tests on MicroPython.

[Targeted qualification, exact commands and input hashes](../root/results/runtime-130-profile/verification.json)

[Stock/patched upstream comparison](../root/results/core-regression-130-qualified/comparison.json)

[Archive, binary and preserved-input integrity checks](../root/results/runtime-130-profile/input-integrity.json)

[Identical patch manifest and source pin](../root/patches/runtime-130/manifest.json)

## Build and dependency details

Both interpreters were built as Windows Win32 Release with MSBuild/v145 from the
same verified source archive. Their labels distinguish the unmodified preview
from our patched runtime:

- `v1.30.0-preview.9a3a0c0d5e`
- `v1.30.0-preview.9a3a0c0d5e-enum980-review`

The patched build uses the same four metaclass feature flags as the 1.29.0 work.
The stock build does not enable those added features. Both use the same empty
frozen-manifest configuration so the comparison isolates the reviewed changes.

The upstream suite uses unittest from the preview's own micropython-lib submodule
pin `ee4bb8ff139e24c42b739935fbd8ec7c4d061e02`, verified against its Git blob hash.
This happens to match the dependency pin in the 1.29.0 qualification.

The six exported patches are identical to the 1.29.0 series. There are no
preview-specific code changes, conflict resolutions or alternative enum paths.
The preview source modifications remain limited to the same eight core files.

## Repeat the run

From enum_980 with CPython 3.12 and the configured Windows build tools:

```powershell
python -B c3b5aae_review/root/src/prepare_runtime_130.py
./c3b5aae_review/root/src/build_runtime_130.ps1
python -B c3b5aae_review/root/src/verify_runtime_130_patches.py
python -B c3b5aae_review/root/src/verify_runtime_130.py
python -B c3b5aae_review/root/src/verify_core_regressions_130.py
python -B c3b5aae_review/root/src/verify_runtime_130_inputs.py
```

Preparation downloads the pinned source archive, checks source version macros,
and reads the exact pinned public unittest blob using gh. Existing reviewed
sources are retained rather than overwritten. Patch checks operate on separate
source copies. Dedicated 130 scripts/results keep the 129 workflow unchanged.

## Limits and publication hold

The runtime-backed profile still requires the core patches. This is not evidence
that it works without them on stock preview. The existing subset restrictions
and wider Enum/metaclass limitations described in the
[1.29.0 review](runtime-129-review.md) remain unchanged.

This qualification is Windows Win32. Unix, physical devices, constrained heaps,
performance and independent review are not newly qualified. A newer preview
snapshot requires another pin and run.

The original project and c3b5aae baseline remain unchanged. No new commits,
pushes or pull requests were made. Publication remains held for user review.
