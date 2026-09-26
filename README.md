# django-bidi-input

Django doesn't let you control the text direction of individual form/admin
input fields — when a site's language is RTL (Farsi, Arabic, Hebrew, ...),
every input renders RTL, including fields where that's wrong: email, URL,
slug, UUID, IP address, numbers, passwords, phone numbers, etc. Only free
text fields should follow the page direction.

This has been an accepted Django ticket
([#35482](https://code.djangoproject.com/ticket/35482)) for a while with no
implementation yet. `django-bidi-input` fixes it today, without patching
Django, for both **admin** and regular **forms**.

## Install

```bash
pip install django-bidi-input
```

```python
INSTALLED_APPS = [
    ...,
    "django_bidi_input",
]
```

That's it. Every `ModelForm`, plain `Form`, and admin form in your project
now gets a correct `dir` attribute (and a `bidi-input-ltr`/`bidi-input-rtl`
CSS class as a fallback) on each field, automatically.

## How direction is decided

For each field, in order (first match wins):

1. You already set `dir` on the widget yourself — left untouched.
2. `direction` set directly on the model field instance:
   ```python
   phone_number = models.CharField(max_length=32)
   phone_number.direction = "ltr"
   ```
3. `BIDI_INPUT_OVERRIDES` setting, for fields you can't edit directly
   (third-party app models, etc.):
   ```python
   BIDI_INPUT_OVERRIDES = {
       "myapp.Contact.phone_number": "ltr",
   }
   ```
4. Built-in default, in order:
   - widget `input_type` is `password`, `number`, `tel`, `date`, `time`, etc.
   - widget `autocomplete` is `username`, `email`, `tel`, `new-password`,
     `current-password`, `one-time-code`. This is what makes Django's own
     admin/auth **login form** (`username` + `password`) render LTR, even
     though `UsernameField` is a plain `CharField` — Django sets
     `autocomplete="username"` on it unconditionally, including when a
     custom user model uses `USERNAME_FIELD = "email"`.
   - field class is `EmailField`, `URLField`, `SlugField`, `UUIDField`,
     `GenericIPAddressField`, `FilePathField`, `IntegerField`, `FloatField`,
     `DecimalField`, `DurationField`, `RegexField`.
5. Otherwise left alone — inherits the page's direction (correct for plain
   `CharField`/`TextField`).

## Settings

| Setting | Default | Purpose |
|---|---|---|
| `BIDI_INPUT_ENABLED` | `True` | Turn the whole thing off. |
| `BIDI_INPUT_OVERRIDES` | `{}` | `"app_label.Model.field": "ltr"/"rtl"` map. |
| `BIDI_INPUT_LTR_FIELD_CLASSES` | see `conf.py` | Dotted paths of extra form field classes to treat as LTR. |
| `BIDI_INPUT_LTR_INPUT_TYPES` | see `conf.py` | Extra widget `input_type` values to treat as LTR. |
| `BIDI_INPUT_LTR_AUTOCOMPLETE_VALUES` | see `conf.py` | Extra widget `autocomplete` values to treat as LTR. |

## Why this works for admin too

Django admin builds its forms as ordinary `ModelForm` subclasses via
`modelform_factory`. This package hooks `BaseForm.__init__` once, so admin
inherits the behavior automatically — no `ModelAdmin` changes needed.

## Scope

This targets the actual pain point: **Django admin and Django forms**.
It does not attempt to make `direction` a real `Field` kwarg (that requires
changing Django itself, which is what ticket #35482 is for), so
introspection-based tools built outside the forms API (DRF serializers,
etc.) won't see it.

## Running the tests

```bash
pip install -e ".[test]"
pytest
```
