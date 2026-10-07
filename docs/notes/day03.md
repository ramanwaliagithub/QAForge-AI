# Day 03
- Page objects live in `framework/pages/`: `BasePage` (open/click/fill helpers), `LoginPage`, `RegisterPage`, `AccountsPage`. Pages hold locators and actions; tests hold assertions.
- `registered_user` is a session fixture that registers a unique ParaBank customer (`qaforge_<uuid>`), so tests don't depend on shared state. Under xdist each worker registers its own user.
- Needed `pythonpath = .` in pytest.ini so `framework` imports resolve.
- xdist `-n 3`: 4 tests in ~8s vs ~10.5s serial. Small gain because setup (registration) is repeated per worker and the demo server is slow.
- The open-account funding dropdown is filled asynchronously; wait for an option before clicking, or the form submits with no source account.
