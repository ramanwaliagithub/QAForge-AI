"""The `data_factory` fixture and the seed it is built from."""
import os
import subprocess
import sys
from pathlib import Path

from framework.data import DataFactory, seed_for_worker

ROOT = Path(__file__).resolve().parent.parent


def test_each_worker_gets_its_own_seed_and_a_serial_run_uses_the_base():
    seeds = [seed_for_worker(100, w) for w in ("master", "gw0", "gw1", "gw2")]
    assert seeds == [100, 101, 102, 103]


def test_workers_with_different_seeds_never_share_a_username():
    names = [{c.username for c in DataFactory(seed_for_worker(5, w)).customers(500)} for w in ("gw0", "gw1", "gw2")]
    assert names[0].isdisjoint(names[1]) and names[1].isdisjoint(names[2]) and names[0].isdisjoint(names[2])


def test_the_fixture_is_seeded_from_the_run_seed(data_factory, request):
    worker = os.environ.get("PYTEST_XDIST_WORKER", "master")
    assert data_factory.seed == seed_for_worker(request.config._data_seed, worker)
    assert data_factory.customers(2) != DataFactory(seed=data_factory.seed + 1000).customers(2)


def _header(*extra):
    """The pytest report header of a collect-only run; addopts is emptied so the child does not wipe allure-results."""
    out = subprocess.run([sys.executable, "-m", "pytest", "-o", "addopts=", "-p", "no:cacheprovider", "--collect-only", *extra,
                          "tests/test_data_models.py"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    return next(line for line in out.splitlines() if line.startswith("test data seed"))


def test_a_seed_given_on_the_command_line_is_the_seed_in_the_header_even_with_workers():
    assert _header("--data-seed=77") == "test data seed: 77 (replay with --data-seed=77)"
    assert _header("--data-seed=77", "-n", "2") == "test data seed: 77 (replay with --data-seed=77)"


def test_without_a_seed_a_random_one_is_chosen_and_printed():
    first, second = _header(), _header()
    assert first.startswith("test data seed: ") and first != second
