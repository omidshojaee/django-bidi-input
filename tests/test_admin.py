import pytest
from django.contrib.admin.sites import AdminSite

from tests.testapp.admin import ContactAdmin, ProfileAdmin
from tests.testapp.models import Contact, Profile


@pytest.mark.django_db
def test_admin_form_gets_directions_without_any_admin_config():
    admin = ContactAdmin(Contact, AdminSite())
    form_class = admin.get_form(request=None)
    form = form_class()

    assert "dir" not in form.fields["full_name"].widget.attrs
    assert form.fields["email"].widget.attrs["dir"] == "ltr"
    assert form.fields["notes"].widget.attrs["dir"] == "rtl"


@pytest.mark.django_db
def test_admin_form_picks_up_settings_override():
    admin = ProfileAdmin(Profile, AdminSite())
    form_class = admin.get_form(request=None)
    form = form_class()

    assert form.fields["bio"].widget.attrs["dir"] == "ltr"
