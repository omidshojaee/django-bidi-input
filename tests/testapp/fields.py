"""Custom form classes for the configuration tests."""

from django import forms


class PhoneField(forms.CharField):
    """A plain text field that a project might want rendered LTR."""


class SearchInput(forms.TextInput):
    input_type = "search"


def not_a_class():
    return None
