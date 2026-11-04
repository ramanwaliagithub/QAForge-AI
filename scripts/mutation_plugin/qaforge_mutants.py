"""pytest plugin for the mutation check: make ParaBank's Bill Pay screen misbehave in ONE chosen way.

Activated by the environment variable QAFORGE_MUTANT=<name> (see MUTANTS); without it the plugin does nothing. It patches
`Browser.new_context` so every browser context gets the mutant's init script or network route. A good test suite for the Bill Pay screen
should fail under every mutant; one that stays green has a blind spot. Load it with `-p qaforge_mutants` and the folder on PYTHONPATH
(scripts/mutation_check.py does both). It lives outside any checkout, so it can score code it did not write.
"""
import json
import os

import pytest
from playwright.sync_api import Browser

BILLPAY = "**/services_proxy/bank/billpay**"


def _style(css: str) -> str:
    """Init script that adds a stylesheet once the DOM exists."""
    return ("document.addEventListener('DOMContentLoaded',()=>{const s=document.createElement('style');"
            f"s.textContent={json.dumps(css)};document.head.appendChild(s)}});")


def _text(element_id: str, text: str) -> str:
    """Init script that replaces the text of one element once the DOM exists."""
    return ("document.addEventListener('DOMContentLoaded',()=>{const e=document.getElementById("
            f"{json.dumps(element_id)});if(e)e.textContent={json.dumps(text)}}});")


# A click on "Send Payment" also fires a payment request, as if validation did not stop a rejected form.
REJECTED_FORM_POSTS = (
    "document.addEventListener('click',e=>{if(e.target&&e.target.value==='Send Payment')"
    "fetch('/parabank/services_proxy/bank/billpay?accountId=0&amount=1',{method:'POST',"
    "headers:{'Content-Type':'application/json'},body:'{}'})},true);"
)

INIT_SCRIPTS = {
    "mismatch_hidden": _style("#validationModel-verifyAccount-mismatch{display:none !important}"),
    "city_required_hidden": _style("#validationModel-city{display:none !important}"),
    "invalid_amount_text_changed": _text("validationModel-amount-invalid", "Invalid."),
    "rejected_form_posts": REJECTED_FORM_POSTS,
}


def _not_debited(route):
    """Answer the payment with a believable success without calling the server: the confirmation shows, no money moves."""
    from urllib.parse import parse_qs, urlparse

    query = parse_qs(urlparse(route.request.url).query)
    body = route.request.post_data_json or {}
    route.fulfill(json={"payeeName": body.get("name", ""), "amount": float(query["amount"][0]), "accountId": int(query["accountId"][0])})


def _debited_twice(route):
    """Send the payment to the server twice (the customer is charged double), answer with the first response."""
    first = route.fetch()
    route.fetch()
    route.fulfill(response=first)


def _tweaked(field: str):
    """Route handler that lets the payment through but changes one field of the confirmation the page shows."""

    def handler(route):
        response = route.fetch()
        body = response.json()
        body[field] = body[field] + 1
        route.fulfill(response=response, json=body)

    return handler


ROUTES = {
    "payment_not_debited": _not_debited,
    "payment_debited_twice": _debited_twice,
    "confirmation_amount_wrong": _tweaked("amount"),
    "confirmation_account_wrong": _tweaked("accountId"),
}
MUTANTS = sorted(set(INIT_SCRIPTS) | set(ROUTES))


def _install(context, mutant: str) -> None:
    """Apply the mutant to a fresh browser context."""
    if mutant in INIT_SCRIPTS:
        context.add_init_script(script=INIT_SCRIPTS[mutant])
    if mutant in ROUTES:
        context.route(BILLPAY, ROUTES[mutant])


def pytest_configure(config):
    """Patch `Browser.new_context` when a mutant is requested; reject an unknown name loudly."""
    mutant = os.environ.get("QAFORGE_MUTANT")
    if not mutant:
        return
    if mutant not in MUTANTS:
        raise pytest.UsageError(f"unknown QAFORGE_MUTANT {mutant!r}; choose from {MUTANTS}")
    original = Browser.new_context

    def new_context(self, *args, **kwargs):
        context = original(self, *args, **kwargs)
        _install(context, mutant)
        return context

    Browser.new_context = new_context
