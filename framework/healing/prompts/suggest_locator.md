A UI test failed because a locator no longer finds its element. The page was redesigned; the test did not change.
Propose ONE replacement locator for the element the test meant.

## What failed
- Failing locator: {locator}
- What the test does with it: {action}
- Failing source lines (innermost last):
{frames}
- Page: {title} ({url})

## Elements currently on the page
Only these exist. Pick the one the test meant, from the code above and its names.
{elements}

## Rules
- Prefer, in this order: role + accessible name, label, visible text, then CSS on an id or a `name` attribute.
- Use CSS only when the element has no accessible name. Never use classes, XPath, positions (nth) or href fragments.
- For buttons use `exact: true` on the role name when one name is a prefix of another.
- The locator must match exactly ONE element on this page.
- Use only elements listed above. Do not invent ids, names or text.

Answer with JSON only, in exactly this shape (leave unused fields out):
{"strategy": "role | label | text | placeholder | css", "role": "button", "name": "Transfer", "exact": true,
 "text": "...", "css": "#id", "reason": "one sentence", "confidence": 0.0}
