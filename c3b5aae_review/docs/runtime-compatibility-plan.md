# Runtime-backed enum compatibility plan

**Goal:** Close the measured typed StrEnum gaps with explicit runtime prerequisites.
**Architecture:** Extend the pinned experimental metaclass runtime, patch general
JSON string-subclass encoding independently, then integrate an opt-in metaclass
StrEnum profile. Preserve the existing stock candidate for comparison.
**Spec:** remaining-boundaries.md, approved in chat by the user.
**Execution:** Direct implementation in this chat, no delegation, commits or pushes.

## Constraints

- All work under c3b5aae_review; original sources remain read-only.
- Runtime base: andrewleech/micropython 6a56288ad12aca9d99d1e425e1400a53c65aa709.
- This is an experimental 1.28.0-preview prerequisite, not stock 1.29.0.
- Separate runtime/library patches and preserve author identity.

## Tasks

- [x] Add general metaclass and JSON regression scripts; record failures on the unmodified runtime.
- [x] Prepare independent source/build under root/build/compat-core with source hashes.
- [x] Implement metaclass subscription, mutation delegation/raw type setters and representation.
- [x] Fix JSON printing for string subclasses as values and keys independently of repr.
- [x] Build and run core regressions, including unchanged ordinary-class behavior.
- [x] Add root/metaclass/enum.py profile using those protocols and protected public metadata.
- [x] Verify class/member identity, length, subscription, selective mutation, representation and JSON against CPython.
- [x] Run original suites and corpus, normal/optimized modes; record precise remaining differences.
- [x] Export reviewable patches and document dependency boundary; keep publication on hold.

## Review focus

- Inherited metaclass methods and hooks delegating to type without recursion.
- Ordinary classes with instance-level dunder methods stay ordinary.
- String-subclass overrides cannot corrupt JSON values/keys; quotes/control/Unicode survive.
- Missing subscription names raise KeyError; member names are protected selectively.
- Public metadata cannot mutate canonical lookup state.

## Outcome

See runtime-profile-review.md for exact evidence, dependency boundaries and
unqualified environments. The runtime-backed profile is separate from the
preserved stock candidate. Publication remains held for user review.
