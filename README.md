# date-planner

Python 3.11+.

Install the candidate validation dependency and run its isolated checks:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
PYTHONPATH=date_agent python -m unittest discover -s tests -v
```

`Candidate` in `date_agent/candidate.py` is a Pydantic model. It validates
field types, enums, positive durations, and seasonal relevance between 0 and 1.
`tags` accepts cuisine, activity types, and general labels without dedicated
fields (for example `japanese`, `live_music`, and `free`). Category, vibe, price,
neighborhood, indoor/outdoor, and source values belong only in their named fields.
Misplaced and unknown tag strings are logged and dropped; they never overwrite or
fill a dedicated field. Invalid optional metadata is logged
and becomes `None`. A missing category defaults to `activity`; an explicitly
invalid category raises `pydantic.ValidationError`, as do invalid content or tag
container types.

`extract_features()` normalizes legacy source fields before validation and
returns a plain dictionary with string enum values and integer effort levels,
so existing scoring functions can keep using `.get()`.

`requirements.txt` currently covers candidate validation only; other application
modules require their own dependencies as they are implemented.
