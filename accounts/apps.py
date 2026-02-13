# ...existing code...
from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        # import signals to register post_save handlers
        import accounts.signals  # noqa: F401
# ...existing code...