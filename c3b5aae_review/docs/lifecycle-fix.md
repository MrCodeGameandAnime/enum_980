# Metaclass lifecycle correction

## Result

The known initialization-order finding is fixed and requalified on actual Unix
standard and Windows Win32 ports for both pinned runtimes. No known blocker from
the final review remains. The documented enum subset and patched-core dependency
requirements still apply.

## Fix

The correction moves metaclass initialization out of `mp_obj_new_type` and into
the outer construction path, after `__new__` returns:

- Direct `type.__new__` performs allocation without calling metaclass `__init__`.
- A completed `__new__` result is initialized only when it is an instance of the
  originally requested metaclass, before base-driven metaclass resolution.
- Initialization uses the actual returned object's metaclass and honors inherited,
  staticmethod and classmethod hooks.
- Exceptions during allocation prevent initialization; initialization exceptions
  propagate, and a non-None initialization result raises TypeError.
- Nested construction keeps each class's allocation and initialization in order.

The new implementation delta touches only `py/objtype.c`. The identical delta
applies to stable and preview sources while retaining the preview's independent
`MP_UNARY_OP_LEN` validation change.

## Regression evidence

Fifteen focused lifecycle cases now run on native CPython and both patched ports,
in normal and optimized modes. They cover declaration/direct/factory construction,
inherited hooks, allocation-only calls, discarded allocations, existing returned
classes, returned subclasses, exceptions, return validation, nested construction,
class-body initialization, descriptor binding and both metaclass-selection edges.

The first 13-case regression was green on CPython and red on the previous
MicroPython builds. Two further cases then exposed the requested-versus-selected
metaclass edge in the first correction. Both were green on CPython and red on that
intermediate correction. The frozen final revision passes all 15.

[Initial failing regressions](../root/results/lifecycle-red/results.json)

[Failing metaclass-selection regressions](../root/results/lifecycle-red/selection-results.json)

## Full qualification

| Port | Version | Upstream tests passed per build | Individual cases per build | Skips |
| --- | --- | ---: | ---: | ---: |
| Windows | 1.29.0 | 549 | 17,403 | 40 |
| Windows | 1.30.0-preview | 551 | 17,425 | 40 |
| Unix | 1.29.0 | 560 | 17,484 | 29 |
| Unix | 1.30.0-preview | 562 | 17,506 | 29 |

Counts apply separately to stock and patched builds. Every comparison has zero
failures and identical skip sets. Each runtime/port also passes the existing
package/profile/hook/parity checks and all 11 DD requirement groups over the
unchanged 61 observations. Qualification requires all 15 lifecycle checks and
all eight general interpreter checks; it cannot accept an optional-feature skip.

The two exported core regression files also pass through the upstream Unix test
runner. Both README examples and the original hook-order reproduction pass on
both Unix versions. A separate INIT-disabled Unix build compiles and correctly
skips the optional lifecycle test. Candidate Python lint passes with the pinned
upstream Ruff configuration.

- [Windows qualification, identities, commands and hashes](../root/results/windows-lifecycle-final-run-20261018T201324Z/qualification.json)
- [Unix qualification, identities, commands and hashes](../root/results/unix/lifecycle-final-run-20261018T201306Z/qualification.json)
- [Final source checks, README examples, exported-test integration and disabled-feature build](../root/results/unix/lifecycle-final-run-20261018T201306Z/final-review-checks.json)
- [Cross-platform hashes and earlier qualification preservation](../root/results/lifecycle-final-integrity.json)

## Review artifacts and repeat commands

Current files are in `root/lifecycle_final/`. Start with
[the patch manifest](../root/lifecycle_final/patches/manifest.json),
[the lifecycle code delta](../root/lifecycle_final/patches/0007-metaclass-lifecycle.patch),
[the regression delta](../root/lifecycle_final/patches/0008-metaclass-lifecycle-tests.patch)
and [clean application evidence](../root/lifecycle_final/patches/application-check.json).
Patches 1-6 retain the preceding final-review versions. Core patches 7 and 8 apply
before the separate library patch 6. The manifest lists the explicit order.

Unix qualification uses the existing pinned Docker image/configuration and
Linux build volume. Run `qualify_unix_lifecycle_final.py` and then
`verify_lifecycle_final_unix.py` in that environment. Windows uses
`qualify_windows_lifecycle_final.py` with CPython 3.12 and the existing MSBuild
configuration. Finally run `verify_lifecycle_final_integrity.py` to check both
reports and preserved inputs. These scripts are under `root/src/`.

An initial Windows harness attempt lacked unittest in the stock source tree and
is recorded as incomplete. The successful Windows comparisons use the prepared,
version-pinned test source and dependency for both runtimes, as in the preceding
qualification. Earlier candidate revisions remain historical evidence.

## Attribution and publication

Andrew Leech's original prerequisite retains its author and Signed-off-by, with
its original patch hash unchanged. IhorNehrutsa's implementation and the DD
adaptation retain their existing credit. New correction/regression work is an
uncommitted user contribution, recorded for
`MrCodeGameAndAnime <MrCodeGameAndAnime@gmail.com>`.

Original tracked project files, the c3b5aae reference, prior source snapshots,
and earlier qualified inputs remain intact. Nothing was committed, pushed,
posted or opened as a PR.
