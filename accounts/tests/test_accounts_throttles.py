from accounts.views import ResendOTPThrottle, LoginThrottle, VerifyOTPThrottle


class DummyRequest:
    def __init__(self, data):
        self.data = data


def test_throttle_cache_key_none_without_email():
    request = DummyRequest({})
    assert ResendOTPThrottle().get_cache_key(request, None) is None
    assert LoginThrottle().get_cache_key(request, None) is None
    assert VerifyOTPThrottle().get_cache_key(request, None) is None


def test_throttle_cache_key_with_email():
    request = DummyRequest({"email": "Test@Example.com"})
    assert ResendOTPThrottle().get_cache_key(request, None) is not None
    assert LoginThrottle().get_cache_key(request, None) is not None
    assert VerifyOTPThrottle().get_cache_key(request, None) is not None
