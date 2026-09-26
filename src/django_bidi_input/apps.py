from django.apps import AppConfig


class BidiInputConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "django_bidi_input"
    verbose_name = "Bidi Input"

    def ready(self):
        from . import patch

        patch.install()
