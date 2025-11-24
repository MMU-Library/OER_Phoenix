from django.apps import AppConfig


class ResourcesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'resources'

    def ready(self):
        # Import signals to attach post_save handlers
        try:
            from . import signals  # noqa: F401
        except Exception:
            pass
