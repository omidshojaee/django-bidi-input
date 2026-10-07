import functools

from django.forms.boundfield import BoundField
from django.forms.forms import BaseForm

from .apply import apply_directions, render_attrs

_PATCHED_ATTR = "_bidi_input_patched"


def _patched(func):
    return getattr(func, _PATCHED_ATTR, False)


def _mark(wrapper):
    setattr(wrapper, _PATCHED_ATTR, True)
    return wrapper


def install():
    """Hook form creation and field rendering. Safe to call more than once."""
    if not _patched(BaseForm.__init__):
        original_init = BaseForm.__init__

        @functools.wraps(original_init)
        def patched_init(self, *args, **kwargs):
            original_init(self, *args, **kwargs)
            apply_directions(self)

        BaseForm.__init__ = _mark(patched_init)

    if not _patched(BoundField.build_widget_attrs):
        original_build = BoundField.build_widget_attrs

        @functools.wraps(original_build)
        def patched_build_widget_attrs(self, attrs, widget=None):
            return render_attrs(self, original_build(self, attrs, widget), widget)

        BoundField.build_widget_attrs = _mark(patched_build_widget_attrs)


def uninstall():
    """Restore Django's own methods (used by the tests)."""
    if _patched(BaseForm.__init__):
        BaseForm.__init__ = BaseForm.__init__.__wrapped__
    if _patched(BoundField.build_widget_attrs):
        BoundField.build_widget_attrs = BoundField.build_widget_attrs.__wrapped__
