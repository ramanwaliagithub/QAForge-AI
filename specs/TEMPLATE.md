# NNN: <what gets built, in a few words>

Status: draft | ready | done        Checked against the app on: YYYY-MM-DD

## Goal

<One paragraph. The outcome, not the method. Who benefits and how you will know.>

## Context

Read these first:
- `<path>`: <why it is the model to copy>
- `<path>`: <what it already provides, so it is not rewritten>

Conventions that apply (point to the source of truth rather than copying it):
- <e.g. `docs/locator-quality-checklist.md`>

Facts about the app that cannot be guessed (verified on the date above):
- <URL or page, exact labels, exact messages, ordering, async behaviour>

## Deliverables

| Path | Change |
|---|---|
| `<path>` | <create / edit: what> |

Public interface:
```python
class Example:
    def method(self, arg: str) -> None: ...
```

## Acceptance criteria

1. <Checkable statement.>
2. <Checkable statement.>

Tests (name: what it asserts):
- `test_<name>`: <the observable outcome it checks>

## Constraints

- <Must hold. e.g. act through the base-class helpers.>

## Out of scope

- <What must not be touched or added.>

## Verification

```bash
<command>     # expect: <result>
```

## Open questions

- <A decision this spec does not make. Ask, or state the assumption you made.>
