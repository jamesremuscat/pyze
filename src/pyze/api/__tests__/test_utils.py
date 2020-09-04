import pytest
from pyze.api.utils import get_api_keys_from_myrenault


def test_simple_grab():
    api_keys = get_api_keys_from_myrenault()
    assert "gigya-api-key" in api_keys
    assert "gigya-api-url" in api_keys
    assert "kamereon-api-key" in api_keys
    assert "kamereon-api-url" in api_keys


def test_locale_grab():
    api_keys = get_api_keys_from_myrenault("fr_FR")
    assert "gigya-api-key" in api_keys
    assert "gigya-api-url" in api_keys
    assert "kamereon-api-key" in api_keys
    assert "kamereon-api-url" in api_keys
