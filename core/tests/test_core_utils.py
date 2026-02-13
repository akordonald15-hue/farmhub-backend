import json
import pytest
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from core.utils.response import api_response, StandardJSONRenderer
from core.logging_utils import get_client_ip, log_event
from core.exceptions import custom_exception_handler


def test_api_response_shape():
    r = api_response(True, "ok", data={"a": 1})
    assert r.status_code == 200
    assert r.data["success"] is True
    assert r.data["message"] == "ok"


def test_standard_renderer_wraps_success():
    renderer = StandardJSONRenderer()
    response = Response({"x": 1}, status=status.HTTP_200_OK)
    rendered = renderer.render(response.data, renderer_context={"response": response, "request": None})
    payload = json.loads(rendered.decode("utf-8"))
    assert payload["success"] is True
    assert payload["data"]["x"] == 1


def test_standard_renderer_wraps_error():
    renderer = StandardJSONRenderer()
    response = Response({"detail": "bad"}, status=status.HTTP_400_BAD_REQUEST)
    rendered = renderer.render(response.data, renderer_context={"response": response, "request": None})
    payload = json.loads(rendered.decode("utf-8"))
    assert payload["success"] is False
    assert payload["errors"]["detail"] == "bad"


def test_custom_exception_handler_wraps_errors():
    exc = ValidationError({"field": ["error"]})
    resp = custom_exception_handler(exc, context={})
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    assert resp.data["success"] is False


def test_logging_utils_ip_and_event(monkeypatch):
    class DummyRequest:
        META = {"REMOTE_ADDR": "127.0.0.1"}
        user = None

    assert get_client_ip(DummyRequest()) == "127.0.0.1"
    log_event("auth_events", DummyRequest(), "test_action", "success")
