import pytest

from framework.locator_audit import Finding, audit_source, classify_css, score


@pytest.mark.parametrize("selector, tier", [
    ("#amount", "id"),
    ("#customer.firstName", "fragile"),  # reads as id + class: a bug in the selector itself
    ("input[name='username']", "name_attr"),
    ("input[name='customer.address.street']", "name_attr"),
    ("[name=password]", "name_attr"),
    ("a[href*='activity.htm']", "fragile"),
    ("p.error", "fragile"),
    ("div.panel > p", "fragile"),
    ("li:nth-child(2)", "fragile"),
    ("//table//a", "fragile"),
    ("xpath=//a", "fragile"),
    ("input[value='Transfer']", "css"),
    ("#fromAccountId option", "css"),
    ("option", "css"),
])
def test_classify_css(selector, tier):
    assert classify_css(selector) == tier


SOURCE = '''
class P:
    def a(self):
        return self.page.get_by_role("button", name="Log In")
    def b(self):
        return self.page.locator("#amount")
    def c(self):
        return self.page.locator("a[href*='x']").first
    def d(self):
        return self.page.locator(f"input[name='{field}']")
    def e(self):
        return self.page.locator(selector_from_variable)
'''


def test_audit_source_finds_and_classifies_every_locator():
    f = audit_source(SOURCE, "p.py")
    assert [(x.call, x.tier) for x in f] == [
        ("get_by_role", "semantic"), ("locator", "id"), ("locator", "fragile"), ("locator", "name_attr"), ("locator", "css"),
    ]
    assert f[1].selector == "#amount" and f[3].selector == "input[name='{}']"  # f-string keeps its shape


def test_position_use_is_flagged():
    f = audit_source(SOURCE, "p.py")
    assert [x.position for x in f] == [False, False, True, False, False]


def test_score_is_mean_tier_value():
    mk = lambda tier: Finding("f", 1, "locator", "", tier)  # noqa: E731
    assert score([mk("semantic"), mk("fragile")]) == 1.5
    assert score([]) == 0.0
