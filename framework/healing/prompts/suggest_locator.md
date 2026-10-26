A UI test failed because a locator no longer finds its element. The page was redesigned; the test did not change.
Propose ONE replacement locator for the element the test meant.

## What failed
- Failing locator: {locator}
- What the test does with it: {action}
- Failing source lines (innermost last):
{frames}
- Page: {title} ({url})

## Candidate elements on the page
Only elements this action can work on are listed. Pick the one the test meant: use the names in the failing source
lines (for example `self.amount`, `self.from_account`, `self.submit_button`) and the old locator to decide.
{elements}

## Rules
- A candidate line shows its ARIA role and accessible name. If it has a name, use strategy "role" with that role and name
  (set `exact: true` for buttons and links).
- If a candidate says "NO accessible name" (typical for form inputs and dropdowns), role/label/text cannot find it:
  use strategy "css" with its id (`#amountId`) or name attribute (`[name='x']`) exactly as listed.
- Never use classes, XPath, positions (nth) or href fragments. Use only candidates listed above; do not invent names or ids.
- The locator must match exactly ONE element on this page.

Answer with ONE JSON object and nothing else. "strategy" must be exactly one of: role, label, text, placeholder, css.
Include only the fields that strategy needs, plus "reason" (one sentence) and "confidence" (0 to 1).

Examples (for a different page; do not copy their values):
{"strategy": "role", "role": "button", "name": "Place order", "exact": true, "reason": "submit button", "confidence": 0.9}
{"strategy": "label", "text": "Email address", "reason": "labelled input", "confidence": 0.8}
{"strategy": "css", "css": "#coupon", "reason": "input without an accessible name; stable id", "confidence": 0.7}
