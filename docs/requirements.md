# DD-derived enum requirements

Reviewed 2026-10-16. This is the requirements baseline for a comparison of native
CPython, DD's original StrEnum overlay, and micropython-lib PR #980.

## Evidence and scope

Static review found **38 direct StrEnum declarations and 231 members** under
DD's `root/src/app/`. These include host-side modules: this is a source census,
not a claim that every declaration runs on the MicroPython deployment target.
All discovered member values are strings and unique within their class.

DD HEAD at review: `2fa5f9d0ca806e5e7dbd41f3ac9073465d26762b`.
The review uses working-tree contents; [dd-enum-census.json](dd-enum-census.json)
records exact source hashes and declaration locations. No game modules were
imported and no tests were executed for this document.

Sources below are DD-relative paths, relative to its `root/` directory.
Existing tests are evidence of intended contracts, not new runtime results.
The supplied Claude report compares CPython with PR head
`f1a9f168ad4bb19a487e54a28c81f77863179560`; it does not measure DD's overlay.

## Required behavior and synthetic cases

Use synthetic `class Mode(StrEnum): FAST = "fast"; SLOW = "slow"` declarations
in executable comparisons. Preserve the behavior of DD's call sites without
importing game modules or copying game models into the comparison runner.

| ID | DD requirement | Game-independent observation | Evidence |
| --- | --- | --- | --- |
| R01 | Members are usable immediately after class definition. | Read `Mode.FAST.name` and `.value` without first calling `Mode()`. | `tests/test_enum_contract.py:84`; authored constants flow straight into validators such as `src/app/content/route_spec.py:53`. |
| R02 | Member name and string value remain distinct and stable. | Expect `"FAST"` and `"fast"`, respectively. | `tests/test_enum_contract.py:88`; serialization uses `.value` in `src/app/player/character_run_state.py:136`. |
| R03 | Lookup by raw value returns the canonical member. | `Mode("fast") is Mode.FAST`; repeat lookup and compare identity. | `tests/test_enum_contract.py:85`; normalization in `src/app/combat/move.py:114`. |
| R04 | Passing an existing member preserves identity. | `Mode(Mode.FAST) is Mode.FAST`. | `tests/test_portable_enum.py:81` and its existing-member lookup regression case. |
| R05 | Invalid string values raise ValueError. | `Mode("missing")` raises `ValueError`. | `tests/test_portable_enum.py:177`; validators catch `ValueError` in `src/app/combat/move.py:117`. |
| R06 | Members are instances of their declared enum class and of str. | `isinstance(Mode.FAST, Mode)` and `isinstance(Mode.FAST, str)`; a raw string is not a `Mode`. | `src/app/content/route_spec.py:53`; explicit enum assertions in `tests/test_enum_contract.py:84`; overlay base is `str`. |
| R07 | String equality and conversion preserve the authored value. | Member/raw-string equality in both directions; `str(Mode.FAST) == "fast"`. | `tests/test_enum_contract.py:90`; string-compatible values are normalized by content and model constructors. Reverse equality is a paired interoperability check. |
| R08 | Enum keys work with raw-string lookup. | `{Mode.FAST: 1}["fast"] == 1`; `hash(Mode.FAST) == hash("fast")`. | `tests/test_enum_contract.py:93`; explicit hashing assertion in `tests/test_portable_enum.py:177`. |
| R09 | Normalization accepts raw values and already-normalized members in sequences. | Normalize tuples of raw strings and members via `Mode(value)`; results retain member identity. | `src/app/combat/move.py:75`; authored-member constructor case in `tests/test_portable_enum.py:68`. |
| R10 | Stored string values can reconstruct typed members. | Store `.value` in a simple document, reconstruct with `Mode(value)`, check identity and type. | `src/app/player/character_run_state.py:136`; `src/app/persistence/save_document.py:169`; `src/app/game/overworld_state.py:116` and `:130`. |
| R11 | Unrelated class bodies keep ordinary behavior. | A plain class retains its string attribute and receives no enum member map. | `tests/test_portable_enum.py:177`; DD intercepts class construction globally. This is a coexistence requirement, not proof that the hook has no other effects. |

The first upstream discussion should emphasize R01, R03, R04 and R06: enum
members are immediately usable typed objects and normalization preserves identity.
R07-R10 explain why merely retaining raw class strings is insufficient.

## Application policies to distinguish from CPython requirements

DD's current declarations use a deliberately limited shape:

- Direct, single inheritance from `StrEnum`.
- Public uppercase member names and explicit literal string values.
- Nonempty enums with unique values; no aliases or custom member methods.

DD's overlay rejects duplicate values, non-string candidate values, and empty
member sets. Its tests explicitly exercise duplicate/non-string rejection.
These are application policies. CPython allows aliases, so an upstream comparison
must report that difference without treating CPython's alias behavior as defective.
No application requirement to reject aliases follows from the declaration census.

## Diagnostic cases, beyond the established DD contract

Keep these visible in a separate compatibility section:

- Name-keyed `__members__`, class subscription, class iteration and iteration order.
- Enum class/member mutation and deletion, aliases, empty classes, non-uppercase names.
- `repr`, functional API, `Enum`, `IntEnum`, and enum subclassing behavior.
- Raw-string-key dictionaries queried using enum members (the reverse of R08).
- Ordinary `str` subclass controls for equality, hash and dictionary lookup in both directions.
- Reimport/hook composition, unrelated classes and other class-building tools.

DD's source-contract test checks for selected direct class subscription and
iteration/length forms, but it is not an exhaustive proof that no indirect use
exists. The current review does not elevate those APIs to application requirements.

Claude's supplied results identify an asymmetric dictionary-lookup difference
that also occurs with an ordinary string subclass on MicroPython. Preserve that
control and record the exact port/build before attributing a failure to enum code.

## What DD contributes, and the costs to measure

DD constructs members as instances of the declared `StrEnum` subclass, assigns
`.name` and `.value`, replaces the declared attributes with those canonical objects,
and installs value lookup. It finalizes direct subclasses during class creation.
This provides a concrete implementation strategy and behavioral use case to study.

Its mechanism replaces `builtins.__build_class__` process-wide and keeps shared
state on `builtins`. That introduces import-order, composition, reimport and
unrelated-class overhead questions. This comparison does not endorse that hook
for upstream adoption, or assume a hook-free equivalent is available.

DD also maps **values to members** in `__members__`, accepts only its chosen member
shape, rejects aliases and provides no explicit immutability guards. It must be
measured against CPython alongside the PR. DD is not the reference oracle.

## Execution contract for the next step

1. Run the same synthetic requirement cases on native CPython, MicroPython with
   an unchanged copy of DD's enum module, and MicroPython with the pinned PR module.
2. Use fresh interpreter processes for implementation modes. Each observation gets
   a fresh enum class; initialization and mutation must not contaminate later observations.
3. Record interpreter name/version, platform, module path, source SHA256 and source
   revision. Verify the intended module was loaded and the PR source matches its pin.
4. Measure immediate access before any explicit initialization. Compare initialization
   adaptations in separate observations, preserving the original requirements.
5. Treat unexpected initialization errors, missing observations and harness-level
   errors as failed measurements. Capture expected language exceptions by type.
6. Keep iteration in declaration order. Include matching outcomes and runtime controls.
7. Report required behavior, application policies, optional API differences and
   interpreter limitations separately. A difference count is not a defect count.
8. Treat memory/firmware-size claims as unmeasured until a separate reproducible
   measurement exists. Do not infer cost from source length.

The outcome should be a three-way evidence table and a small reproducible package
suitable for a maintainer discussion. Posting comments or submitting changes upstream
is a separate action; nothing is sent as part of this requirements review.

## Reference files

- DD `portability/micropython/enum.py`: original implementation, unchanged.
- DD `tests/test_enum_contract.py` and `tests/test_portable_enum.py`: contract evidence.
- Historical two-way comparisons and extraction-audit recommendations are summarized
  in [Background](background.md). Their relevant constraints and hook concerns are
  stated above; the original local research files are not required or distributed.
- [PR #980](https://github.com/micropython/micropython-lib/pull/980): upstream discussion;
  reproducible implementation reference is the pinned commit, not the moving PR head.

## Declaration census

| Class | Members | DD source location |
| --- | ---: | --- |
| `MoveKind` | 3 | `src/app/combat/move.py:9` |
| `ResourceType` | 3 | `src/app/combat/move.py:15` |
| `ScalingAttribute` | 7 | `src/app/combat/move.py:21` |
| `TargetType` | 2 | `src/app/combat/move.py:31` |
| `DamageType` | 5 | `src/app/combat/move.py:36` |
| `MoveRole` | 5 | `src/app/combat/move_presentation.py:7` |
| `CombatOutcomeType` | 41 | `src/app/combat/result.py:7` |
| `CombatOutcomeTarget` | 2 | `src/app/combat/result.py:51` |
| `StatusKind` | 8 | `src/app/combat/status_state.py:20` |
| `RouteNodeKind` | 4 | `src/app/content/route_spec.py:28` |
| `EnemyRank` | 4 | `src/app/enemies/definition.py:4` |
| `EnemyRole` | 7 | `src/app/enemies/definition.py:11` |
| `EnemyBehavior` | 1 | `src/app/enemies/definition.py:21` |
| `EnemyCapability` | 5 | `src/app/enemies/definition.py:25` |
| `OverworldSessionResult` | 1 | `src/app/game/overworld_session.py:49` |
| `ContextualRoutePhase` | 3 | `src/app/game/overworld_state.py:21` |
| `SyncState` | 4 | `src/app/persistence/envelope.py:33` |
| `LegacyMigrationStatus` | 5 | `src/app/persistence/migration.py:23` |
| `ProfileStoreStatus` | 3 | `src/app/persistence/ports.py:17` |
| `ConflictStoreStatus` | 3 | `src/app/persistence/ports.py:23` |
| `SaveLoadStatus` | 5 | `src/app/persistence/save_port_contract.py:8` |
| `RunItemId` | 3 | `src/app/player/character_run_state.py:7` |
| `PreparedPayloadId` | 1 | `src/app/player/character_run_state.py:13` |
| `InfusionKind` | 2 | `src/app/player/character_run_state.py:17` |
| `InventoryActionId` | 2 | `src/app/player/character_run_state.py:22` |
| `InventoryActionRejectionReason` | 3 | `src/app/player/inventory_action.py:12` |
| `InventoryCommand` | 2 | `src/app/player/run_items.py:15` |
| `ActionIntent` | 6 | `src/app/presentation/battle_models.py:10` |
| `InteractionPhase` | 11 | `src/app/presentation/battle_models.py:19` |
| `InputRejectionReason` | 9 | `src/app/presentation/battle_models.py:33` |
| `BattleEventType` | 13 | `src/app/presentation/battle_models.py:45` |
| `ActionAvailabilityReason` | 7 | `src/app/presentation/battle_models.py:61` |
| `MoveAvailabilityReason` | 2 | `src/app/presentation/battle_models.py:71` |
| `InventoryAvailabilityReason` | 3 | `src/app/presentation/battle_models.py:76` |
| `OverworldScreen` | 13 | `src/app/presentation/overworld_models.py:7` |
| `OverworldAction` | 21 | `src/app/presentation/overworld_models.py:23` |
| `OverworldAvailabilityReason` | 9 | `src/app/presentation/overworld_models.py:47` |
| `MapNodeState` | 3 | `src/app/presentation/overworld_models.py:59` |
