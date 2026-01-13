import config
from crawler import is_url_in_module


def test_is_url_in_module_matches_seed_and_subpath():
    module = "PawMatch"
    seed = config.MODULES[module][0]
    assert is_url_in_module(seed, module)
    assert is_url_in_module(seed.rstrip("/") + "/profile", module)


def test_is_url_in_module_rejects_other_module():
    module = "PawMatch"
    other_seed = config.MODULES["GroomUp"][0]
    assert not is_url_in_module(other_seed, module)
