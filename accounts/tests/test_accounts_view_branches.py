import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from accounts.models import EmailVerification

User = get_user_model()


@pytest.mark.django_db
def test_verify_email_missing_verification_record(client):
    user = User.objects.create_user(
        email="verify_missing@example.com",
        password="StrongPass123",
        full_name="Verify Missing",
    )
    EmailVerification.objects.filter(user=user).delete()
    r = client.post("/api/accounts/verify-email/", data={"email": user.email, "otp": "123456"})
    assert r.status_code == 400


@pytest.mark.django_db
def test_verify_email_attempt_limit(client):
    user = User.objects.create_user(
        email="verify_attempts@example.com",
        password="StrongPass123",
        full_name="Verify Attempts",
    )
    verification = EmailVerification.objects.get(user=user)
    verification.otp = "123456"
    verification.otp_expires_at = timezone.now() + timezone.timedelta(minutes=5)
    verification.otp_attempts = 5
    verification.save(update_fields=["otp", "otp_expires_at", "otp_attempts"])

    r = client.post("/api/accounts/verify-email/", data={"email": user.email, "otp": "123456"})
    assert r.status_code == 400


@pytest.mark.django_db
def test_resend_otp_missing_verification_record(client):
    user = User.objects.create_user(
        email="resend_missing@example.com",
        password="StrongPass123",
        full_name="Resend Missing",
    )
    EmailVerification.objects.filter(user=user).delete()
    r = client.post("/api/accounts/resend-otp/", data={"email": user.email})
    assert r.status_code == 400


@pytest.mark.django_db
def test_resend_otp_send_mail_failure(client, monkeypatch):
    user = User.objects.create_user(
        email="resend_fail@example.com",
        password="StrongPass123",
        full_name="Resend Fail",
    )

    def boom(*args, **kwargs):
        raise Exception("mail fail")

    monkeypatch.setattr("accounts.views.send_mail", boom)
    r = client.post("/api/accounts/resend-otp/", data={"email": user.email})
    assert r.status_code == 200


@pytest.mark.django_db
def test_register_triggers_email_send(client, monkeypatch):
    called = {"value": False}

    def fake_send(*args, **kwargs):
        called["value"] = True
        return 1

    monkeypatch.setattr("accounts.views.send_mail", fake_send)
    payload = {
        "email": "register_send@example.com",
        "password": "StrongPass123",
        "password2": "StrongPass123",
        "full_name": "Register Send",
        "username": "register_send",
        "role": "customer",
    }
    r = client.post("/api/accounts/register/", data=payload)
    assert r.status_code == 201
    assert called["value"] is True


@pytest.mark.django_db
def test_register_resets_verified_flag(client, monkeypatch):
    def noop_send(*args, **kwargs):
        return 1

    monkeypatch.setattr("accounts.views.send_mail", noop_send)

    original_get = EmailVerification.objects.get

    def fake_get(*args, **kwargs):
        obj = original_get(*args, **kwargs)
        obj.is_verified = True
        obj.save(update_fields=["is_verified"])
        return obj

    monkeypatch.setattr(EmailVerification.objects, "get", fake_get)
    payload = {
        "email": "register_reset@example.com",
        "password": "StrongPass123",
        "password2": "StrongPass123",
        "full_name": "Register Reset",
        "username": "register_reset",
        "role": "customer",
    }
    r = client.post("/api/accounts/register/", data=payload)
    assert r.status_code == 201
    user = User.objects.get(email="register_reset@example.com")
    verification = EmailVerification.objects.filter(user=user).first()
    assert verification.is_verified is False


@pytest.mark.django_db
def test_register_send_mail_failure(client, monkeypatch):
    def boom(*args, **kwargs):
        raise Exception("mail fail")

    monkeypatch.setattr("accounts.views.send_mail", boom)
    payload = {
        "email": "register_fail@example.com",
        "password": "StrongPass123",
        "password2": "StrongPass123",
        "full_name": "Register Fail",
        "username": "register_fail",
        "role": "customer",
    }
    r = client.post("/api/accounts/register/", data=payload)
    assert r.status_code == 201
