import importlib
import importlib.util
import os


def test_backend_entrypoints_import(monkeypatch):
    # Minimal env to allow settings imports
    monkeypatch.setenv("SECRET_KEY", "test-secret")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("ALLOWED_HOSTS", "localhost,127.0.0.1")
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000")
    monkeypatch.setenv("CSRF_TRUSTED_ORIGINS", "http://localhost:3000")
    monkeypatch.setenv("REDIS_URL", "redis://127.0.0.1:6379/1")
    monkeypatch.setenv("EMAIL_HOST_USER", "user")
    monkeypatch.setenv("EMAIL_HOST_PASSWORD", "pass")
    monkeypatch.setenv("EMAIL_HOST", "smtp.example.com")
    monkeypatch.setenv("DEFAULT_FROM_EMAIL", "test@example.com")
    monkeypatch.setenv("DEBUG", "True")
    monkeypatch.setenv("DB_NAME", "test")
    monkeypatch.setenv("DB_USER", "test")
    monkeypatch.setenv("DB_PASSWORD", "test")
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv("DB_PORT", "5432")

    import backend.asgi
    import backend.wsgi
    import backend.settings
    import backend.settings.prod

    importlib.reload(backend.asgi)
    importlib.reload(backend.wsgi)
    importlib.reload(backend.settings)
    importlib.reload(backend.settings.prod)

    # manage.py lives at repo root; import via module loader path
    manage_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "manage.py")
    manage_path = os.path.abspath(manage_path)
    spec = importlib.util.spec_from_file_location("manage", manage_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # legacy backend/settings.py (file) is shadowed by backend.settings package
    legacy_settings_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "backend", "settings.py")
    legacy_settings_path = os.path.abspath(legacy_settings_path)
    legacy_spec = importlib.util.spec_from_file_location("backend_settings_legacy", legacy_settings_path)
    legacy_module = importlib.util.module_from_spec(legacy_spec)
    legacy_spec.loader.exec_module(legacy_module)
