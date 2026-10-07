from django.apps import AppConfig
from django.core import checks


class BidiInputConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "django_bidi_input"
    verbose_name = "Bidi Input"

    def ready(self):
        from . import patch
        from .checks import check_settings

        patch.install()
        checks.register(check_settings)
