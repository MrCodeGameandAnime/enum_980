# Background

This investigation grew out of Dungeon Drifters' MicroPython portability work.

1. The extraction audit identified dataclass metadata as a standalone-library
   candidate and enum behavior as an area for upstream contributions.
2. The supplied initial comparison measured CPython against PR #980. It provided
   useful background, but did not measure DD's own implementation.
3. The [requirements review](requirements.md) traced DD's actual enum declarations,
   validators and existing tests. The source census records 38 classes and 231 members.
4. The [three-way comparison](comparison.md) ran the same synthetic observations
   against CPython, DD's unchanged overlay and the pinned #980 implementation.

The original audit and supplied scripts are local historical research material,
not distributed with this repository. Their relevant conclusions are summarized
above and in the requirements review; they are not required to execute the comparison. Current requirements,
source records, runner code and measured results are under `docs/` and `root/`.

## Source records

Each candidate snapshot has a `source.json` file containing its revision, origin
and file hash. The measured-result JSON files use a `sources` section for the
interpreter and candidate source records. These establish which exact files were
used; they do not assert that either candidate is fully CPython compatible.

Recorded execution commands and paths describe the original runs, including the
folder name used at the time. Renaming the project folder does not change those
historical measurements.
