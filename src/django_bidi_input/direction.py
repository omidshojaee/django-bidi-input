from django.core.exceptions import FieldDoesNotExist

from . import conf

LTR = "ltr"
RTL = "rtl"
VALID_DIRECTIONS = (LTR, RTL)


def _override_key(model, field_name):
    return "{}.{}.{}".format(model._meta.app_label, model._meta.object_name, field_name)


def _model_field_for(model, field_name):
    if model is None:
        return None
    try:
        return model._meta.get_field(field_name)
    except FieldDoesNotExist:
        return None


def resolve_direction(form_field, field_name, model=None):
    model_field = _model_field_for(model, field_name)

    if model_field is not None:
        direction = getattr(model_field, "direction", None)
        if direction in VALID_DIRECTIONS:
            return direction

    if model is not None:
        override = conf.get_overrides().get(_override_key(model, field_name))
        if override in VALID_DIRECTIONS:
            return override

    input_type = getattr(form_field.widget, "input_type", None)
    if input_type in conf.get_ltr_input_types():
        return LTR

    autocomplete = form_field.widget.attrs.get("autocomplete")
    if autocomplete in conf.get_ltr_autocomplete_values():
        return LTR

    if isinstance(form_field, conf.get_ltr_field_classes()):
        return LTR

    return None
