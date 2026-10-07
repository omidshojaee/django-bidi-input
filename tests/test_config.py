"""Settings: extending, tolerating bad values, system checks."""

import pytest
from django import forms
from django.test import override_settings

from django_bidi_input.checks import check_settings
from django_bidi_input.conf import build_config
from tests.testapp.models import Contact, Profile

PHONE = "tests.testapp.fields.PhoneField"


def dirs(form):
    return {name: f.widget.attrs.get("dir") for name, f in form.fields.items()}


class TextForm(forms.Form):
    date = forms.DateField()  # LTR by default (field class)
    password = forms.CharField(widget=forms.PasswordInput)  # LTR by default (input type)
    username = forms.CharField(widget=forms.TextInput(attrs={"autocomplete": "username"}))
    text = forms.CharField()


class CustomForm(forms.Form):
    from tests.testapp.fields import PhoneField, SearchInput

    phone = PhoneField()
    search = forms.CharField(widget=SearchInput)
    card = forms.CharField(widget=forms.TextInput(attrs={"autocomplete": "cc-number"}))


def profile_form():
    return forms.modelform_factory(Profile, fields=["bio"])()


# --- the LTR_* settings add to the defaults, they do not replace them -------


def test_extra_field_classes_extend_the_defaults():
    with override_settings(BIDI_INPUT_LTR_FIELD_CLASSES=[PHONE]):
        assert dirs(CustomForm())["phone"] == "ltr"
        assert dirs(TextForm())["date"] == "ltr"  # the default is still there


def test_extra_input_types_extend_the_defaults():
    with override_settings(BIDI_INPUT_LTR_INPUT_TYPES=["search"]):
        assert dirs(CustomForm())["search"] == "ltr"
        assert dirs(TextForm())["password"] == "ltr"


def test_extra_autocomplete_values_extend_the_defaults():
    with override_settings(BIDI_INPUT_LTR_AUTOCOMPLETE_VALUES=["cc-number"]):
        assert dirs(CustomForm())["card"] == "ltr"
        assert dirs(TextForm())["username"] == "ltr"


def test_without_the_extra_settings_those_fields_are_left_alone():
    assert dirs(CustomForm()) == {"phone": None, "search": None, "card": None}


def test_a_single_string_counts_as_a_one_item_list():
    with override_settings(BIDI_INPUT_LTR_FIELD_CLASSES=PHONE):
        assert dirs(CustomForm())["phone"] == "ltr"
    with override_settings(BIDI_INPUT_LTR_INPUT_TYPES="search"):
        assert dirs(CustomForm())["search"] == "ltr"


def test_extra_values_are_case_and_whitespace_tolerant():
    with override_settings(BIDI_INPUT_LTR_INPUT_TYPES=[" SEARCH "]):
        assert dirs(CustomForm())["search"] == "ltr"


def test_a_class_object_is_accepted_in_place_of_a_dotted_path():
    from tests.testapp.fields import PhoneField

    with override_settings(BIDI_INPUT_LTR_FIELD_CLASSES=[PhoneField]):
        assert dirs(CustomForm())["phone"] == "ltr"


def test_changing_a_setting_takes_effect_immediately_and_is_undone():
    assert dirs(CustomForm())["phone"] is None
    with override_settings(BIDI_INPUT_LTR_FIELD_CLASSES=[PHONE]):
        assert dirs(CustomForm())["phone"] == "ltr"
    assert dirs(CustomForm())["phone"] is None


def test_enabled_switch():
    with override_settings(BIDI_INPUT_ENABLED=False):
        assert set(dirs(TextForm()).values()) == {None}
    assert dirs(TextForm())["date"] == "ltr"


# --- bad values never break a form -----------------------------------------


@pytest.mark.parametrize(
    "value",
    [
        ["django.forms.EmailFeild"],  # typo
        ["django.utils.timezone.now"],  # a function, not a class
        ["nonsense"],  # no dot at all
        "a.b.c.",  # string with dots
        [42, None],  # not even strings
        42,  # not a list
    ],
)
def test_bad_field_class_settings_never_crash_a_form(value):
    with override_settings(BIDI_INPUT_LTR_FIELD_CLASSES=value):
        assert dirs(TextForm())["date"] == "ltr"  # defaults still work
        assert dirs(TextForm())["text"] is None


@pytest.mark.parametrize("setting", ["BIDI_INPUT_LTR_INPUT_TYPES", "BIDI_INPUT_LTR_AUTOCOMPLETE_VALUES"])
@pytest.mark.parametrize("value", [42, [None, 3], {"a": 1}])
def test_bad_value_settings_never_crash_a_form(setting, value):
    with override_settings(**{setting: value}):
        assert dirs(TextForm())["password"] == "ltr"


@pytest.mark.parametrize("value", [["ltr"], "ltr", 5, [("a.B.c", "ltr")]])
def test_a_non_dict_overrides_setting_never_crashes_a_model_form(value):
    with override_settings(BIDI_INPUT_OVERRIDES=value):
        assert dirs(profile_form())["bio"] is None


def test_a_widget_with_class_none_does_not_crash():
    class F(forms.Form):
        n = forms.IntegerField(widget=forms.NumberInput(attrs={"class": None}))

    form = F()
    assert form.fields["n"].widget.attrs["dir"] == "ltr"
    assert form.fields["n"].widget.attrs["class"] == "bidi-input-ltr"


# --- overrides: tolerant of case and of the label_lower form ---------------


@pytest.mark.parametrize(
    "key, value",
    [
        ("testapp.Profile.bio", "ltr"),
        ("testapp.profile.bio", "ltr"),  # label_lower
        ("TESTAPP.PROFILE.BIO", " LTR "),
    ],
)
def test_override_keys_and_values_are_case_insensitive(key, value):
    with override_settings(BIDI_INPUT_OVERRIDES={key: value}):
        assert dirs(profile_form())["bio"] == "ltr"


def test_override_can_be_auto_and_rtl():
    with override_settings(BIDI_INPUT_OVERRIDES={"testapp.Profile.bio": "auto"}):
        assert dirs(profile_form())["bio"] == "auto"
    with override_settings(BIDI_INPUT_OVERRIDES={"testapp.Profile.bio": "rtl"}):
        assert dirs(profile_form())["bio"] == "rtl"


def test_an_invalid_override_value_is_skipped_so_the_default_logic_applies():
    with override_settings(BIDI_INPUT_OVERRIDES={"testapp.Contact.email": "sideways"}):
        form = forms.modelform_factory(Contact, fields=["email"])()
        assert dirs(form)["email"] == "ltr"  # EmailField default, not the bad value


# --- system checks ---------------------------------------------------------


def check_ids():
    return sorted(message.id for message in check_settings())


def test_the_test_projects_own_settings_are_clean():
    assert check_settings() == []


def test_checks_report_unimportable_and_non_class_paths():
    with override_settings(
        BIDI_INPUT_LTR_FIELD_CLASSES=["django.forms.EmailFeild", "django.utils.timezone.now"]
    ):
        assert check_ids() == ["django_bidi_input.W001", "django_bidi_input.W002"]


def test_checks_report_invalid_override_values_and_keys():
    with override_settings(BIDI_INPUT_OVERRIDES={"testapp.Profile.bio": "sideways", "bio": "ltr"}):
        assert check_ids() == ["django_bidi_input.W003", "django_bidi_input.W005"]


def test_checks_report_settings_of_the_wrong_type():
    with override_settings(BIDI_INPUT_LTR_INPUT_TYPES=42, BIDI_INPUT_OVERRIDES=["x"]):
        assert check_ids() == ["django_bidi_input.W004", "django_bidi_input.W004"]


def test_checks_report_an_invalid_direction_on_a_model_field():
    field = Contact._meta.get_field("full_name")
    field.direction = "sideways"
    try:
        found = [m for m in check_settings() if m.id == "django_bidi_input.W006"]
    finally:
        del field.direction
    assert len(found) == 1 and "full_name" in found[0].msg


def test_checks_are_registered_with_djangos_check_framework():
    from django.core import checks

    with override_settings(BIDI_INPUT_LTR_FIELD_CLASSES=["nonsense"]):
        ids = [m.id for m in checks.run_checks()]
    assert "django_bidi_input.W001" in ids


def test_build_config_reports_the_same_problems_the_checks_show():
    with override_settings(BIDI_INPUT_LTR_FIELD_CLASSES=["nonsense"]):
        assert [kind for kind, _ in build_config().problems] == ["import"]
