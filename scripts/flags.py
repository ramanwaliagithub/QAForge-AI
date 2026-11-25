"""Command-line flags for the scripts: `--name=value` and bare `--name`, in one place instead of a copy in every script.

Options are `--name=value`, never `--name value`: the same rule as for pytest (CLAUDE.md), and it keeps positional arguments unambiguous.
"""


def parse_flags(argv: list[str], usage: str | None = None) -> tuple[dict[str, str], list[str]]:
    """Split `argv` into flags and positional arguments. `--a=1 --b x` gives ({"a": "1", "b": "1"}, ["x"]); a bare flag has the value "1".

    With `usage` given, `--help` prints it and exits instead of letting the script run: a script that deletes or rewrites reports must not start by accident.
    """
    flags: dict[str, str] = {}
    positional: list[str] = []
    for arg in argv:
        if arg.startswith("--"):
            name, _, value = arg[2:].partition("=")
            flags[name] = value if "=" in arg else "1"
        else:
            positional.append(arg)
    if usage and "help" in flags:
        print(usage)
        raise SystemExit(0)
    return flags, positional
