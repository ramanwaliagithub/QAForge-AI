# Healing review

Updated 2026-10-28T05:58:21+00:00. 1 proposals: 1 proposed, 0 approved, 0 rejected, 0 applied.

Each proposal is a locator that failed at run time and was replaced, in memory only, by an LLM suggestion that worked when the step was retried. **No source file has been changed.** The score is a transparent heuristic (components shown), not a probability. Approve with `python -m framework.healing approve <id>`, then `python -m framework.healing apply`.

## 1. `74be18c8`  PROPOSED  score 1.00

- **Old:** `locator("#amt")`
- **New:** `locator("#amount")`  (css; fill)
- **Why (model):** old locator was for an input without an accessible name; stable id  (self-reported confidence 0.9)
- **Defined at:** `framework/pages/transfer_page.py:13`  `return self.page.locator("#amt")`
- **Resolved element:** tag='input', type='text', id='amount', name='input'
- **Tests affected (3):** `test_decimal_amount_is_accepted`, `test_negative_amount_is_rejected`, `test_transfer_larger_than_balance_is_rejected`
- **Score:** base 0.50, retry_verified +0.20, first_attempt +0.10, semantic_locator +0.05, one_source_definition +0.10, repeated_across_tests +0.10, harness_repair +0.00, model_self_report +0.04
- **Flag:** non_semantic_locator: css; tests/test_locator_quality.py will need an ACCEPTED entry with a reason

```diff
--- a/framework/pages/transfer_page.py
+++ b/framework/pages/transfer_page.py
@@ -11,5 +11,5 @@
     @property
     def amount(self):
-        return self.page.locator("#amt")
+        return self.page.locator("#amount")
 
     @property
```

