"""Settings for django-bidi-input.

Settings are read once, normalised and cached; the cache is dropped whenever a
``BIDI_INPUT_*`` setting changes (``override_settings`` in tests, for example).

A bad value never raises while a form is being built. It is skipped, and
``manage.py check`` reports it (see ``checks.py``).
"""

from collections.abc import Mapping
from dataclasses import dataclass

from django.conf import settings
from django.core.signals import setting_changed
from django.utils.module_loading import import_string

LTR = "ltr"
RTL = "rtl"
AUTO = "auto"
VALID_DIRECTIONS = (LTR, RTL, AUTO)

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


@dataclass(frozen=True)
class Config:
    enabled: bool
    field_classes: tuple
    input_types: frozenset
    autocomplete_values: frozenset
    overrides: dict  # lower-cased "app_label.model.field" -> direction
    problems: tuple  # (kind, message) for every value that had to be skipped


def normalize_direction(value):
    """``"ltr"`` / ``"rtl"`` / ``"auto"`` (any case, padded) or ``None``."""
    if isinstance(value, str):
        value = value.strip().lower()
        if value in VALID_DIRECTIONS:
            return value
    return None


def _items(name, value, problems):
    """A setting that should be a list; a bare string counts as one item."""
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    try:
        return list(value)
    except TypeError:
        problems.append(
            ("type", f"{name} must be a list, not {type(value).__name__}; ignored.")
        )
        return []


def _load_classes(paths, problems):
    classes = []
    for path in paths:
        if isinstance(path, type):
            classes.append(path)
            continue
        try:
            obj = import_string(path)
        except (ImportError, ValueError, AttributeError, TypeError) as exc:
            problems.append(("import", f"{path!r} could not be imported ({exc})."))
            continue
        if isinstance(obj, type):
            classes.append(obj)
        else:
            problems.append(("class", f"{path!r} is not a class; ignored."))
    return classes


def build_config():
    """Read and validate the settings (uncached)."""
    problems = []

    extra_classes = _load_classes(
        _items(
            "BIDI_INPUT_LTR_FIELD_CLASSES",
            getattr(settings, "BIDI_INPUT_LTR_FIELD_CLASSES", None),
            problems,
        ),
        problems,
    )
    default_classes = _load_classes(DEFAULT_LTR_FIELD_PATHS, [])
    field_classes = tuple(dict.fromkeys([*default_classes, *extra_classes]))

    input_types = set(DEFAULT_LTR_INPUT_TYPES)
    input_types.update(
        str(item).strip().lower()
        for item in _items(
            "BIDI_INPUT_LTR_INPUT_TYPES",
            getattr(settings, "BIDI_INPUT_LTR_INPUT_TYPES", None),
            problems,
        )
    )

    autocomplete_values = set(DEFAULT_LTR_AUTOCOMPLETE_VALUES)
    autocomplete_values.update(
        str(item).strip().lower()
        for item in _items(
            "BIDI_INPUT_LTR_AUTOCOMPLETE_VALUES",
            getattr(settings, "BIDI_INPUT_LTR_AUTOCOMPLETE_VALUES", None),
            problems,
        )
    )

    raw_overrides = getattr(settings, "BIDI_INPUT_OVERRIDES", None) or {}
    overrides = {}
    if not isinstance(raw_overrides, Mapping):
        problems.append(
            (
                "type",
                "BIDI_INPUT_OVERRIDES must be a dict of "
                '"app_label.Model.field": "ltr"/"rtl"/"auto"; ignored.',
            )
        )
        raw_overrides = {}
    for key, value in raw_overrides.items():
        direction = normalize_direction(value)
        if direction is None:
            problems.append(
                (
                    "direction",
                    f"BIDI_INPUT_OVERRIDES[{key!r}] = {value!r} is not one of "
                    "'ltr', 'rtl', 'auto'; ignored.",
                )
            )
            continue
        key = str(key).strip().lower()
        if key.count(".") != 2:
            problems.append(
                (
                    "key",
                    f"BIDI_INPUT_OVERRIDES key {key!r} should look like "
                    '"app_label.Model.field"; it will never match.',
                )
            )
        overrides[key] = direction

    return Config(
        enabled=bool(getattr(settings, "BIDI_INPUT_ENABLED", True)),
        field_classes=field_classes,
        input_types=frozenset(input_types),
        autocomplete_values=frozenset(autocomplete_values),
        overrides=overrides,
        problems=tuple(problems),
    )


_cache = None


def get_config():
    global _cache
    if _cache is None:
        _cache = build_config()
    return _cache


def _reset(*, setting=None, **kwargs):
    global _cache
    if setting is None or setting.startswith("BIDI_INPUT_"):
        _cache = None


setting_changed.connect(_reset, dispatch_uid="django_bidi_input.conf.reset")


# Convenience accessors (kept for backwards compatibility).


def get_ltr_field_classes():
    return get_config().field_classes


def get_ltr_input_types():
    return set(get_config().input_types)


def get_ltr_autocomplete_values():
    return set(get_config().autocomplete_values)


def get_overrides():
    return dict(get_config().overrides)


def is_enabled():
    return get_config().enabled
