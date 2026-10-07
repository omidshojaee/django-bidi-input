"""System checks: report settings and model fields the package has to skip.

Forms never fail because of a bad setting; ``manage.py check`` (and
``runserver``) print these warnings instead.
"""

from django.apps import apps
from django.core import checks

from . import conf

_IDS = {
    "import": "django_bidi_input.W001",
    "class": "django_bidi_input.W002",
    "direction": "django_bidi_input.W003",
    "type": "django_bidi_input.W004",
    "key": "django_bidi_input.W005",
}
MODEL_FIELD_DIRECTION_ID = "django_bidi_input.W006"


def check_settings(app_configs=None, **kwargs):
    messages = [
        checks.Warning(message, id=_IDS[kind])
        for kind, message in conf.build_config().problems
    ]

    for model in apps.get_models():
        for field in model._meta.get_fields():
            direction = getattr(field, "direction", None)
            if direction is not None and conf.normalize_direction(direction) is None:
                messages.append(
                    checks.Warning(
                        f"{model._meta.label}.{field.name}.direction = {direction!r} "
                        "is not one of 'ltr', 'rtl', 'auto'; it is ignored.",
                        obj=field,
                        id=MODEL_FIELD_DIRECTION_ID,
                    )
                )
    return messages
