from pyze.api.credentials import BasicCredentialStore


class TestBasicCredentialStore:
    def test_new(self):
        credentials = BasicCredentialStore()
        assert "gigya-api-key" not in credentials
        assert "gigya-api-url" not in credentials
        assert "kamereon-api-key" not in credentials
        assert "kamereon-api-url" not in credentials

        credentials.get_api_keys_from_myrenault()
        assert "gigya-api-key" in credentials
        assert "gigya-api-url" in credentials
        assert "kamereon-api-key" in credentials
        assert "kamereon-api-url" in credentials
