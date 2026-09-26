from django.forms.forms import BaseForm

from .apply import apply_directions

_PATCHED_ATTR = "_bidi_input_patched"


def install():
    if getattr(BaseForm.__init__, _PATCHED_ATTR, False):
        return

    original_init = BaseForm.__init__

    def patched_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        apply_directions(self)

    setattr(patched_init, _PATCHED_ATTR, True)
    BaseForm.__init__ = patched_init
