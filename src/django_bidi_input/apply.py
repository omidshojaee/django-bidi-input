from . import conf
from .direction import resolve_direction


def _with_marker(css_class, direction):
    tokens = str(css_class).split() if css_class else []
    marker = "bidi-input-{}".format(direction)
    if marker not in tokens:
        tokens.append(marker)
    return " ".join(tokens)


def _model_of(form):
    return getattr(getattr(form, "_meta", None), "model", None)


def apply_directions(form):
    """Set ``dir`` (and a ``bidi-input-*`` class) on the widgets of ``form``."""
    if not conf.get_config().enabled:
        return

    model = _model_of(form)

    for field_name, field in form.fields.items():
        attrs = field.widget.attrs

        if attrs.get("dir"):
            continue

        direction = resolve_direction(field, field_name, model=model)
        if direction is None:
            continue

        attrs["dir"] = direction
        attrs["class"] = _with_marker(attrs.get("class"), direction)


def render_attrs(bound_field, attrs, widget=None):
    """Render-time fallback for ``BoundField.build_widget_attrs``.

    ``apply_directions`` runs when the form is created, so it cannot see a field
    that is added later or a widget that is replaced later (a formset's ``ORDER``
    field, a form that swaps widgets in its own ``__init__``). This catches those
    when the field is rendered. It never touches a widget that already has a
    ``dir``.
    """
    if not conf.get_config().enabled:
        return attrs

    widget = widget or bound_field.field.widget
    if attrs.get("dir") or widget.attrs.get("dir"):
        return attrs

    direction = resolve_direction(
        bound_field.field,
        bound_field.name,
        model=_model_of(bound_field.form),
        widget=widget,
    )
    if direction is None:
        return attrs

    attrs = dict(attrs)
    attrs["dir"] = direction
    # Django lets render-time attrs replace the widget's own, class included.
    current = attrs["class"] if "class" in attrs else widget.attrs.get("class")
    attrs["class"] = _with_marker(current, direction)
    return attrs
