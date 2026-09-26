from django import forms
import pytest

from tests.testapp.models import Contact, Profile


class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = [
            "full_name",
            "email",
            "website",
            "slug",
            "reference_id",
            "ip_address",
            "age",
            "notes",
            "phone_number",
        ]


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["bio"]


class PlainForm(forms.Form):
    subject = forms.CharField()
    contact_email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)


@pytest.mark.django_db
def test_plain_text_field_is_left_alone():
    form = ContactForm()
    assert "dir" not in form.fields["full_name"].widget.attrs


@pytest.mark.django_db
@pytest.mark.parametrize(
    "field_name",
    ["email", "website", "slug", "reference_id", "ip_address", "age"],
)
def test_builtin_heuristic_defaults_to_ltr(field_name):
    form = ContactForm()
    assert form.fields[field_name].widget.attrs["dir"] == "ltr"


@pytest.mark.django_db
def test_explicit_model_field_override_rtl():
    form = ContactForm()
    assert form.fields["notes"].widget.attrs["dir"] == "rtl"


@pytest.mark.django_db
def test_explicit_model_field_override_ltr_for_plain_charfield():
    # phone_number is a bare CharField; only the .direction attribute
    # set on the model field in models.py makes it LTR.
    form = ContactForm()
    assert form.fields["phone_number"].widget.attrs["dir"] == "ltr"


@pytest.mark.django_db
def test_settings_override_map():
    form = ProfileForm()
    assert form.fields["bio"].widget.attrs["dir"] == "ltr"


def test_plain_non_model_form_uses_class_based_heuristic():
    form = PlainForm()
    assert "dir" not in form.fields["subject"].widget.attrs
    assert form.fields["contact_email"].widget.attrs["dir"] == "ltr"
    assert form.fields["password"].widget.attrs["dir"] == "ltr"


def test_admin_login_form_username_and_password_are_ltr():
    from django.contrib.auth.forms import AuthenticationForm

    form = AuthenticationForm()
    # UsernameField is a plain CharField -- only the autocomplete="username"
    # token (set by Django itself) makes this resolve to LTR. This also
    # covers a custom user model with USERNAME_FIELD = "email": Django's
    # AuthenticationForm always uses UsernameField regardless of the
    # underlying model field type, so the field-class heuristic alone
    # would never catch it.
    assert form.fields["username"].widget.attrs["dir"] == "ltr"
    assert form.fields["password"].widget.attrs["dir"] == "ltr"


def test_developer_set_dir_is_never_overwritten():
    class ExplicitForm(forms.Form):
        note = forms.CharField(widget=forms.TextInput(attrs={"dir": "rtl"}))

    form = ExplicitForm()
    assert form.fields["note"].widget.attrs["dir"] == "rtl"
