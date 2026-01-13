import config


def test_homepage_url_configured():
    assert config.WEBSITE_URL
    assert config.WEBSITE_URL.startswith("http")
