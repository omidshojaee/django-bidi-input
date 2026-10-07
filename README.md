# django-bidi-input

Django doesn't let you control the text direction of individual form/admin
input fields — when a site's language is RTL (Farsi, Arabic, Hebrew, ...),
every input renders RTL, including fields where that's wrong: email, URL,
slug, UUID, IP address, numbers, passwords, phone numbers, etc. Only free
text fields should follow the page direction.

This has been an accepted Django ticket
([#35482](https://code.djangoproject.com/ticket/35482)) for a while with no
implementation yet. `django-bidi-input` fixes it today, for both **admin**
and regular **forms**. You don't fork or edit Django: at startup the package
wraps two of its methods (`BaseForm.__init__` and
`BoundField.build_widget_attrs`), and the wrappers can be removed again.

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
now gets a correct `dir` attribute (and a `bidi-input-ltr` / `bidi-input-rtl` /
`bidi-input-auto` CSS class, a hook for your own styling; the package ships no
CSS) on each field, automatically.

## How direction is decided

For each field, in order (first match wins):

1. You already set `dir` on the widget yourself — left untouched.
2. `direction` set directly on the model field instance (`"ltr"`, `"rtl"` or
   `"auto"`, any case):
   ```python
   phone_number = models.CharField(max_length=32)
   phone_number.direction = "ltr"
   ```
3. `BIDI_INPUT_OVERRIDES` setting, for fields you can't edit directly
   (third-party app models, etc.). Keys are `app_label.Model.field`, in any
   case; values are `"ltr"`, `"rtl"` or `"auto"`:
   ```python
   BIDI_INPUT_OVERRIDES = {
       "myapp.Contact.phone_number": "ltr",
   }
   ```
4. Built-in default, in order:
   - widget `input_type` is `password`, `number`, `tel`, `date`, `time`, etc.
   - widget `autocomplete` contains one of `username`, `email`, `tel`,
     `new-password`, `current-password`, `one-time-code`. `autocomplete` is a
     list of tokens, so `"shipping email"` and `"username webauthn"` match
     too. This is what makes Django's own admin/auth **login form**
     (`username` + `password`) render LTR, even though `UsernameField` is a
     plain `CharField` — Django sets `autocomplete="username"` on it
     unconditionally, including when a custom user model uses
     `USERNAME_FIELD = "email"`.
   - field class is `EmailField`, `URLField`, `SlugField`, `UUIDField`,
     `GenericIPAddressField`, `FilePathField`, `IntegerField`, `FloatField`,
     `DecimalField`, `DurationField`, `RegexField`, `JSONField`, `DateField`,
     `DateTimeField`, `TimeField`, `SplitDateTimeField` (the two-input widget
     admin uses for `DateTimeField` by default — `dir` propagates to both
     boxes). Date/time fields need this class-based check specifically
     because Django's date/time widgets render as `<input type="text">`,
     not native HTML5 `type="date"`/`type="time"`, even in admin.
5. Otherwise left alone — inherits the page's direction (correct for plain
   `CharField`/`TextField`). Hidden inputs are always left alone.

The direction is applied twice, so nothing slips through. When a form is
created, the widget's `attrs` get `dir`, so you can inspect them. When a field
is rendered, anything that was added or changed after creation (a widget
swapped in your form's `__init__`, a formset's `ORDER` field) is caught too.
A `dir` you set yourself is never overwritten.

## Settings

| Setting | Default | Purpose |
|---|---|---|
| `BIDI_INPUT_ENABLED` | `True` | Turn the whole thing off. |
| `BIDI_INPUT_OVERRIDES` | `{}` | `"app_label.Model.field": "ltr"/"rtl"/"auto"` map. |
| `BIDI_INPUT_LTR_FIELD_CLASSES` | `[]` | Dotted paths of **extra** form field classes to treat as LTR (added to the built-in list). |
| `BIDI_INPUT_LTR_INPUT_TYPES` | `[]` | **Extra** widget `input_type` values to treat as LTR. |
| `BIDI_INPUT_LTR_AUTOCOMPLETE_VALUES` | `[]` | **Extra** widget `autocomplete` tokens to treat as LTR. |

The three `LTR` settings add to the built-in lists shown above; they never
replace them. To keep one specific field out of the defaults, set `dir` on its
widget (or a `direction` / `BIDI_INPUT_OVERRIDES` entry).

A wrong value never breaks a form: the bad entry is skipped. `manage.py check`
(and `runserver`) tell you about it, with these warnings:

| ID | Meaning |
|---|---|
| `django_bidi_input.W001` | A dotted path could not be imported (a typo). |
| `django_bidi_input.W002` | A dotted path is not a class. |
| `django_bidi_input.W003` | A `BIDI_INPUT_OVERRIDES` value is not `ltr`, `rtl` or `auto`. |
| `django_bidi_input.W004` | A setting has the wrong type. |
| `django_bidi_input.W005` | A `BIDI_INPUT_OVERRIDES` key is not `app_label.Model.field`. |
| `django_bidi_input.W006` | A model field's `direction` is not `ltr`, `rtl` or `auto`. |

## Why this works for admin too

Django admin builds its forms as ordinary `ModelForm` subclasses via
`modelform_factory`, and renders them through the same `BoundField`. The two
hooks above cover forms and admin alike — no `ModelAdmin` changes needed.

## Scope

This targets the actual pain point: **Django admin and Django forms**.
It does not attempt to make `direction` a real `Field` kwarg (that requires
changing Django itself, which is what ticket #35482 is for), so
introspection-based tools built outside the forms API (DRF serializers,
etc.) won't see it.

Fields from other packages are covered by the settings above. For example, to
render [django-jalali-suite](https://pypi.org/project/django-jalali-suite/)'s
date inputs LTR:

```python
BIDI_INPUT_LTR_FIELD_CLASSES = [
    "jalali_suite.forms.JalaliDateField",
    "jalali_suite.forms.JalaliDateTimeField",
    "jalali_suite.forms.SplitJalaliDateTimeField",
]
```

## Running the tests

```bash
pip install -e ".[test]"
pytest
```
