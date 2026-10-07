"""Fields the form-creation hook cannot see, and what ends up in the HTML."""

import inspect

import pytest
from django import forms
from django.forms import formset_factory
from django.forms.boundfield import BoundField
from django.forms.forms import BaseForm
from django.test import override_settings

from django_bidi_input import patch
from tests.testapp.models import Contact


class SwapsWidgets(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ["email", "age"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Typical styling code: replace the widget, add a field afterwards.
        self.fields["email"].widget = forms.EmailInput(attrs={"class": "form-control"})
        self.fields["extra"] = forms.IntegerField()
        self.fields["note"] = forms.CharField()


def html(form, name):
    return str(form[name])


# --- late changes are caught when the field is rendered --------------------


def test_a_widget_replaced_in_init_still_renders_ltr_and_keeps_its_class():
    rendered = html(SwapsWidgets(), "email")
    assert 'dir="ltr"' in rendered
    assert 'class="form-control bidi-input-ltr"' in rendered


def test_a_field_added_in_init_renders_ltr():
    assert 'dir="ltr"' in html(SwapsWidgets(), "extra")


def test_plain_text_fields_added_late_stay_alone():
    assert "dir=" not in html(SwapsWidgets(), "note")


def test_formset_order_field_renders_ltr_and_delete_does_not():
    class Row(forms.Form):
        name = forms.CharField()

    formset = formset_factory(Row, can_order=True, can_delete=True, extra=1)()
    form = formset.forms[0]

    assert 'dir="ltr"' in str(form["ORDER"])
    assert "dir=" not in str(form["DELETE"])
    assert "dir=" not in str(form["name"])


def test_render_time_attrs_replace_the_widgets_class_like_django_does():
    rendered = SwapsWidgets()["extra"].as_widget(attrs={"class": "mine"})
    assert 'class="mine bidi-input-ltr"' in rendered


def test_a_developers_own_dir_is_never_overwritten_at_render_time():
    form = SwapsWidgets()
    form.fields["extra"].widget = forms.NumberInput(attrs={"dir": "rtl"})
    assert 'dir="rtl"' in html(form, "extra")
    assert 'dir="ltr"' not in html(form, "extra")


def test_a_dir_passed_when_rendering_wins():
    rendered = SwapsWidgets()["extra"].as_widget(attrs={"dir": "rtl"})
    assert 'dir="rtl"' in rendered and 'dir="ltr"' not in rendered


def test_disabling_the_package_disables_the_render_time_fallback_too():
    with override_settings(BIDI_INPUT_ENABLED=False):
        assert "dir=" not in html(SwapsWidgets(), "email")


def test_form_creation_and_rendering_do_not_duplicate_the_class_marker():
    class F(forms.Form):
        n = forms.IntegerField()

    form = F()
    rendered = html(form, "n")
    assert form.fields["n"].widget.attrs["class"] == "bidi-input-ltr"
    assert rendered.count("bidi-input-ltr") == 1


# --- values and the class marker -------------------------------------------


@pytest.mark.parametrize(
    "value",
    ["shipping email", "username webauthn", "section-x billing tel", "EMAIL", "  work   tel  "],
)
def test_autocomplete_is_read_as_a_token_list(value):
    class F(forms.Form):
        x = forms.CharField(widget=forms.TextInput(attrs={"autocomplete": value}))

    assert F().fields["x"].widget.attrs["dir"] == "ltr"


@pytest.mark.parametrize("value", ["shipping name", "off", "on", "", "section-x"])
def test_autocomplete_without_an_ltr_token_is_left_alone(value):
    class F(forms.Form):
        x = forms.CharField(widget=forms.TextInput(attrs={"autocomplete": value}))

    assert "dir" not in F().fields["x"].widget.attrs


def test_auto_is_a_valid_direction_on_a_model_field():
    field = Contact._meta.get_field("full_name")
    field.direction = "auto"
    try:
        class F(forms.ModelForm):
            class Meta:
                model = Contact
                fields = ["full_name"]

        form = F()
    finally:
        del field.direction

    assert form.fields["full_name"].widget.attrs["dir"] == "auto"
    assert 'dir="auto"' in html(form, "full_name")
    assert "bidi-input-auto" in html(form, "full_name")


def test_a_model_field_direction_is_case_insensitive():
    field = Contact._meta.get_field("full_name")
    field.direction = " RTL "
    try:
        class F(forms.ModelForm):
            class Meta:
                model = Contact
                fields = ["full_name"]

        assert F().fields["full_name"].widget.attrs["dir"] == "rtl"
    finally:
        del field.direction


def test_hidden_inputs_get_no_direction():
    class F(forms.Form):
        pk = forms.IntegerField(widget=forms.HiddenInput)

    form = F()
    assert "dir" not in form.fields["pk"].widget.attrs
    assert "dir=" not in html(form, "pk")


def test_the_class_marker_is_added_next_to_existing_classes_only_once():
    class F(forms.Form):
        e = forms.EmailField(widget=forms.EmailInput(attrs={"class": "vTextField  wide"}))

    assert F().fields["e"].widget.attrs["class"] == "vTextField wide bidi-input-ltr"


def test_the_class_marker_matches_the_direction():
    class F(forms.Form):
        e = forms.EmailField()

    assert 'class="bidi-input-ltr"' in html(F(), "e")


# --- the patch itself -------------------------------------------------------


def test_the_patched_methods_keep_djangos_name_docstring_and_signature():
    assert BaseForm.__init__.__name__ == "__init__"
    assert BoundField.build_widget_attrs.__name__ == "build_widget_attrs"
    assert BaseForm.__init__.__module__ == "django.forms.forms"
    assert BoundField.build_widget_attrs.__module__ == "django.forms.boundfield"
    assert str(inspect.signature(BaseForm.__init__)).startswith("(self, data=None")
    assert str(inspect.signature(BoundField.build_widget_attrs)) == "(self, attrs, widget=None)"
    # functools.wraps leaves a trail back to Django's own function
    assert BaseForm.__init__.__wrapped__.__qualname__ == "BaseForm.__init__"


def test_install_is_idempotent_and_uninstall_restores_django():
    before = (BaseForm.__init__, BoundField.build_widget_attrs)
    try:
        patch.install()
        patch.install()
        assert (BaseForm.__init__, BoundField.build_widget_attrs) == before

        patch.uninstall()
        assert not hasattr(BaseForm.__init__, "__wrapped__")  # plain Django again
        assert not hasattr(BoundField.build_widget_attrs, "__wrapped__")

        class F(forms.Form):
            e = forms.EmailField()

        assert "dir" not in F().fields["e"].widget.attrs
        assert "dir=" not in str(F()["e"])
    finally:
        patch.install()

    class G(forms.Form):
        e = forms.EmailField()

    assert G().fields["e"].widget.attrs["dir"] == "ltr"
