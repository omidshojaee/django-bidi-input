from django.core.exceptions import FieldDoesNotExist

from . import conf
from .conf import AUTO, LTR, RTL, VALID_DIRECTIONS  # noqa: F401  (public names)


def _model_field_for(model, field_name):
    if model is None:
        return None
    try:
        return model._meta.get_field(field_name)
    except FieldDoesNotExist:
        return None


def _autocomplete_is_ltr(value, ltr_values):
    """``autocomplete`` is a list of space separated tokens ("shipping email")."""
    if not isinstance(value, str):
        return False
    return any(token in ltr_values for token in value.lower().split())


def resolve_direction(form_field, field_name, model=None, widget=None):
    """Return ``"ltr"``, ``"rtl"``, ``"auto"`` or ``None`` (leave it alone)."""
    widget = widget or form_field.widget
    if widget.is_hidden:
        return None

    config = conf.get_config()
    model_field = _model_field_for(model, field_name)

    if model_field is not None:
        direction = conf.normalize_direction(getattr(model_field, "direction", None))
        if direction:
            return direction

    if model is not None:
        direction = config.overrides.get(f"{model._meta.label_lower}.{field_name}".lower())
        if direction:
            return direction

    if getattr(widget, "input_type", None) in config.input_types:
        return LTR

    if _autocomplete_is_ltr(widget.attrs.get("autocomplete"), config.autocomplete_values):
        return LTR

    if isinstance(form_field, config.field_classes):
        return LTR

    return None
