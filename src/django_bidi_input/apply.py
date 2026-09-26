from . import conf
from .direction import resolve_direction


def apply_directions(form):
    if not conf.is_enabled():
        return

    model = getattr(getattr(form, "_meta", None), "model", None)

    for field_name, field in form.fields.items():
        attrs = field.widget.attrs

        if attrs.get("dir"):
            continue

        direction = resolve_direction(field, field_name, model=model)
        if direction is None:
            continue

        attrs["dir"] = direction
        css_class = attrs.get("class", "")
        marker = "bidi-input-{}".format(direction)
        if marker not in css_class.split():
            attrs["class"] = "{} {}".format(css_class, marker).strip()
