# Specs

A spec is a short document that tells a coding agent (or a person) **what to build, what already exists, how to know it is
done, and what to leave alone**. It is written for a reader that has no memory of earlier conversations and will not ask
questions unless told to. A vague prompt ("add BillPay tests") makes the agent guess; a spec makes the guesses unnecessary.

Specs live in `specs/NNN-short-name.md` (three digits, in the order they were written). Copy `TEMPLATE.md` to start one.

## The format

Every spec has these sections, in this order. Delete none; write "none" where a section is empty, so a reader can tell
"nothing here" from "forgot".

| Section | What goes in it | The mistake it prevents |
|---|---|---|
| **Goal** | One paragraph: the outcome a user or the suite gets, not the method. | The agent solves a different problem. |
| **Context** | What exists today (files to read first), the conventions that apply, and **facts about the app that cannot be guessed**, each with the date it was checked. | Invented selectors, invented messages, duplicated helpers. |
| **Deliverables** | Exact paths to create or change, and the public interface (class and method names, signatures). | Files in the wrong place, names that do not match the rest of the code. |
| **Acceptance criteria** | A numbered list. Each item is something you can check with a command or by looking at one thing. Tests are listed by name with what each one asserts. | "Done" meaning "looks plausible". |
| **Constraints** | Rules that must hold (use the existing helpers, no sleeps, no new dependencies). | Style drift, hidden coupling. |
| **Out of scope** | What the agent must not touch or add, even if it looks useful. | Scope creep and unrelated edits that are hard to review. |
| **Verification** | The exact commands to run and what a good result looks like. | The agent reporting success without running anything. |
| **Open questions** | Decisions the spec does not make. The agent must ask or state its assumption, not silently pick. | Silent guesses. |

## Rules for writing one

1. **Acceptance criteria must be checkable.** "Tests are robust" is not checkable. "No `time.sleep`, no `.nth()`; `pytest -n 3` passes
   3 times in a row" is.
2. **Put app facts in the spec, with a date.** If the real error text is "Payee name is required.", write that string. An agent
   that has to discover it from the page will sometimes get it wrong, and one that cannot reach the page will invent it.
3. **Say where to look, not just what to do.** Name the one or two existing files that are the model to copy.
4. **Say what is out of scope as firmly as what is in.** Agents add things; reviewers pay for them.
5. **Specify the interface, leave the internals open.** Names and signatures are contracts; how a method is written is not.
6. **A spec is a file in git.** Change it when the requirement changes, and keep the version that produced the code you merged.
7. **A spec overrides `CLAUDE.md` where they conflict, silently.** Spec 001 fixed its form fields to `name` attributes (waiving rule L2) and asked only for
   "no confirmation" in rejection tests (waiving T4), and the agent that had read both followed the spec each time (`docs/notes/day19.md`). If a spec
   waives a repo rule, say so under Constraints; otherwise write the spec so it does not forbid one.

## Using a spec

Give the agent the path, not a summary: "Implement `specs/001-billpay-page-and-tests.md`. Do not change files outside its Deliverables.
Tell me about any criterion you could not meet." Then judge the result against the **Acceptance criteria** and **Verification**
sections, not against how it reads. `docs/notes/day18.md` records the first comparison of a spec against a vague prompt.
