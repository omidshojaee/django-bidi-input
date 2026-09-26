from django.conf import settings
from django.utils.module_loading import import_string

DEFAULT_LTR_FIELD_PATHS = [
    "django.forms.EmailField",
    "django.forms.URLField",
    "django.forms.SlugField",
    "django.forms.UUIDField",
    "django.forms.GenericIPAddressField",
    "django.forms.FilePathField",
    "django.forms.IntegerField",
    "django.forms.FloatField",
    "django.forms.DecimalField",
    "django.forms.DurationField",
    "django.forms.RegexField",
    "django.forms.JSONField",
    "django.forms.DateField",
    "django.forms.DateTimeField",
    "django.forms.TimeField",
    "django.forms.SplitDateTimeField",
]

DEFAULT_LTR_INPUT_TYPES = {
    "email",
    "url",
    "number",
    "password",
    "tel",
    "date",
    "time",
    "datetime-local",
    "month",
    "week",
    "color",
}

DEFAULT_LTR_AUTOCOMPLETE_VALUES = {
    "username",
    "email",
    "tel",
    "new-password",
    "current-password",
    "one-time-code",
}


def _import_all(dotted_paths):
    classes = []
    for path in dotted_paths:
        try:
            classes.append(import_string(path))
        except ImportError:
            continue
    return tuple(classes)


def get_ltr_field_classes():
    paths = getattr(settings, "BIDI_INPUT_LTR_FIELD_CLASSES", DEFAULT_LTR_FIELD_PATHS)
    return _import_all(paths)


def get_ltr_input_types():
    return set(getattr(settings, "BIDI_INPUT_LTR_INPUT_TYPES", DEFAULT_LTR_INPUT_TYPES))


def get_ltr_autocomplete_values():
    return set(
        getattr(
            settings,
            "BIDI_INPUT_LTR_AUTOCOMPLETE_VALUES",
            DEFAULT_LTR_AUTOCOMPLETE_VALUES,
        )
    )


def get_overrides():
    return getattr(settings, "BIDI_INPUT_OVERRIDES", {})


def is_enabled():
    return getattr(settings, "BIDI_INPUT_ENABLED", True)
