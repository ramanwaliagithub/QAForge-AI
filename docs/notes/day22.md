# Day 22: Test data with AI

Branch `day-22-test-data`, issue #25. Code in `framework/data/`, comparison in `scripts/compare_data_sources.py`, numbers in `reports/day22/day22.json`.

## What I built
- **Models with strict rules** (`models.py`): an `Identity` (name, street, city, state, zip, phone, SSN) and a `Customer` (identity plus username and password). The rules are ours:
  ParaBank accepts nearly any text, so "the form took it" proves little.
- **Three interchangeable sources of identities**: Faker (seeded), a model (`LLMSource`), and a frozen JSON file (`FrozenSource`). The model source validates each item, drops and counts
  the bad ones, and asks again for the shortfall with the reasons.
- **A seeded `DataFactory`.** Who a person is comes from the source; what must be unique or exact (username, password, money) always comes from the factory's own generator,
  so a model that repeats itself cannot cause a collision. `seed=None` picks a seed and keeps it. In pytest: a `data_factory` fixture, `--data-seed`, the seed in the report header,
  one derived seed per xdist worker.

## Faker against a model (llama3.1:8b, 30 people, 3 model runs)
| | Faker | Model |
|---|---|---|
| Items valid on first sight | 100% | **43%, 47%, 75%** (the rest were rejected by the rules and re-asked: 2 to 4 calls per 30 people) |
| Time for 30 people | 0.02 s | **56 to 113 s** (median 83 s) |
| Same seed, same people | yes | **no**: two runs share 0% of their names |
| Variety (share of distinct values) | names 0.97, phone endings 1.0, SSN endings 1.0 | last names 0.47 to 0.93, phone endings 0.17 to 0.33, SSN endings 0.2 to 0.87 |
| Registered in ParaBank, name shown as given | 30 / 30 | 30 / 30 |

- The model's usual mistake was the phone number: `210-555-1234` with punctuation (62 of the rejected items over the first two runs). SSNs and cities were the other rejections.
- What the model did better: its people look real. City, state, zip and area code agree (Chicago, IL, 60601, 312), and the names are a real mix (O'Connor, Patel, Singh).
  Faker's cities, states and zips are unrelated (`Johnsonfurt, NE 90743`).
- What it did worse: it repeats itself. One run returned the same SSN (`321-45-6789`) on several people and phone numbers that end alike. These are made-up values with a pattern.

## When AI data helps, and when it hurts
- **Helps** when the application *looks at* the data being realistic: address or zip validation, a name that has to fit a layout, screenshots and demos, an exploratory pass for
  odd-but-valid values. ParaBank validates none of this, so here the realism bought nothing a test could notice.
- **Hurts** when a test must repeat (not reproducible), when it must be fast (about 4000 times slower here), when values must be unique or exact (repeats, punctuation), and in
  any test where a wrong value would be mistaken for an app bug. It also adds a failure mode: the model server being down.
- **Rule I took from it:** Faker is the default; a model writes a dataset once, a person reads it, and it is committed as a frozen file. Tests use the file, never the model. Money,
  usernames and boundary values are never model-written.

## The best finding came from neither source
Probing why my "name shown as given" check failed (I had read the wrong page: after registering, the page greets the username) I tried a name with an accent. ParaBank answers
**HTTP 400, "Character decoding failed"** to `Siobhán`. An apostrophe and a hyphen are fine. So the name rules are ASCII, `tests/test_registration_data.py` holds a strict xfail for the accent,
and the model prompt now says "no accents". A model that writes diverse names would have walked straight into this.

## Limits
- One model, one prompt, 3 runs of 30. Validity numbers move with the prompt; they say nothing about other models.
- The prompt gained the "no accents" line **after** the three generation runs; the registration check used the last of those runs (all ASCII, by luck of that sample).
- Faker is en_US only. "Accepted by ParaBank" means the form took it, not that every later page showed it correctly (only the welcome line was checked).
- Not wired into the older fixtures: `registered_user` and `new_customer_page` still register the fixed "Qa Forge", on purpose, because changing who every UI test logs in as
  is a change to the whole suite, and a seeded name there buys nothing.
- No reviewed frozen dataset is committed yet: the first model sample repeated SSNs, so it would need editing by hand first. The mechanism (`save_identities`, `FrozenSource`) is tested.
