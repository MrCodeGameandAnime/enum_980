# Findings for an upstream enum discussion

Measured locally on CPython 3.12.14 and the native Windows port of MicroPython
1.29.0. See [the full comparison](comparison.md) and
[raw results](three-way-results.json) for exact sources, observations and sources.
This is a synthetic requirements comparison, not an execution of DD's full game.

## The contribution DD demonstrates

DD's unchanged overlay matches the CPython reference for all 11 requirement groups
(18 individual required observations). The pinned PR matches 5 groups without
application changes. These are overlapping requirement groups, not independent bug
counts or a score for full enum compatibility.

DD demonstrates an implementation that produces real instances of the declared
StrEnum subclass immediately after class definition on this MicroPython build.
It preserves existing-member identity through normalization and supports a
stored-string-to-typed-member round trip. No metaclass implementation was added.

The mechanism is concrete: instantiate the declared string subclass for each member,
attach its name and value, install the canonical objects on the class, then replace
construction with value lookup. DD invokes this finalizer through a process-wide
class-builder hook. That hook is the cost and integration question to discuss;
its performance, memory cost and compatibility with other hooks are not measured here.

## What initializing the PR first changes

The PR's documented no-argument initialization step resolves immediate name/value
access and the observed existing-member/sequence normalization differences.
Before initialization, class attributes are raw strings; references captured then
remain those original strings when the class attributes are replaced.

Initialization does not make its members instances of the declared enum class.
The PR creates a separate value-type subclass for each member. The prepared
serialization case restores canonical identity but still fails its enum-class
instance check. This is the central semantic question left after accounting for
the PR's documented initialization adaptation.

## Where DD also differs from CPython

- `__members__` maps values to members instead of names to members.
- Class subscription, iteration and length are unavailable in this subset.
- Duplicate values are rejected, rather than becoming aliases.
- Empty classes and lowercase-only member declarations are rejected.
- Class member reassignment/deletion and member `.value` mutation are allowed.
- Member repr is the underlying string repr.

Those results prevent treating DD as an interchangeable standard-library enum
implementation or as the reference oracle. They do not erase the narrower behavior
it demonstrates for upstream consideration.

## Runtime controls and measurement limits

Both candidates reproduce a reverse dictionary lookup failure on the same Windows
MicroPython build: a dictionary with a raw string key cannot be queried with the
matching string-subclass instance. The ordinary str-subclass control reproduces it
without enum code. The other lookup direction, required by DD's tests, passes.
This result should be discussed as an interpreter behavior with recorded port and build.

Effective builtin lookup detects DD's class-builder replacement. On this build,
explicit `builtins.__build_class__` attribute access continues to expose the original;
the runner retains both observations. The runner's regression test checks that the
hook is not falsely reported absent.

The upstream candidate differs in iteration order even through its instance-based
iteration interface. The comparison preserves declaration order and does not sort
away that difference.

## Suggested maintainer questions

1. Is immediately usable StrEnum class syntax a goal for the supported subset?
2. Should members satisfy `isinstance(member, DeclaredEnum)`? DD has a real validator
   requiring this, and the small synthetic case reproduces the requirement.
3. Can the typed-member finalization mechanism inform upstream work while using a
   class-finalization mechanism acceptable to maintainers?
4. Which remaining differences are accepted subset boundaries, and which should
   receive CPython-reference tests before an implementation is selected?

The reproduction files are ready for local review. No comment, issue, fork, or PR
has been created or sent upstream by this work.
