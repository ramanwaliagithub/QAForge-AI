"""The element a person would pick for each broken-locator sample. Used only to score the suggester, never in prompts.

Keys are sample names (the part after `test_sample_` / `test_heldout_` in the test id). Values are attributes of the
element description Playwright returns for the healed locator (see suggestion._DESCRIBE_JS).
"""
TUNED = {
    "id_renamed": {"id": "amount"},
    "button_text_changed": {"tag": "input", "type": "submit", "value": "Transfer"},
    "locator_too_generic": {"id": "fromAccountId"},
}

# Written after the prompt was tuned on TUNED; never edit the prompt while looking at these.
HELDOUT = {
    "username_renamed": {"name": "username"},
    "logout_link_renamed": {"tag": "a", "text": "Log Out"},
    "account_type_dropdown": {"id": "type"},
    "first_name_field_renamed": {"name": "customer.firstName"},
}

# Set 2: written after set 1 had been used to diagnose the suggester, so it is the unbiased measurement.
HELDOUT2 = {
    "password_renamed": {"name": "password"},
    "register_button_renamed": {"tag": "input", "type": "submit", "value": "Register"},
    "state_field_renamed": {"name": "customer.address.state"},
    "to_account_id_renamed": {"id": "toAccountId"},
}

# Set 3: written after sets 1 and 2 had been used to diagnose and fix the suggester. The unbiased one.
HELDOUT3 = {
    "login_button_renamed": {"tag": "input", "type": "submit", "value": "Log In"},
    "last_name_field_renamed": {"name": "customer.lastName"},
    "phone_field_renamed": {"name": "customer.phoneNumber"},
    "funding_account_renamed": {"id": "fromAccountId"},
}

# Controls where no locator change is the right answer (an assertion failed, or the element legitimately changed).
CONTROLS = ["expect_on_missing_element", "wrong_text_on_found_element"]


def matches(element: dict, truth: dict) -> bool:
    return all(element.get(k) == v for k, v in truth.items())
