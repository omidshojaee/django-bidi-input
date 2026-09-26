from django.db import models


class Contact(models.Model):
    # Plain text: should stay RTL when the site/admin language is RTL.
    full_name = models.CharField(max_length=100)

    # Covered by the built-in heuristic (input_type/field-class default): LTR.
    email = models.EmailField()
    website = models.URLField(blank=True)
    slug = models.SlugField()
    reference_id = models.UUIDField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    age = models.PositiveIntegerField(null=True, blank=True)

    # Explicit per-field override set directly on the model field instance.
    notes = models.TextField(blank=True)
    notes.direction = "rtl"

    phone_number = models.CharField(max_length=32, blank=True)
    phone_number.direction = "ltr"

    class Meta:
        app_label = "testapp"


class Profile(models.Model):
    contact = models.OneToOneField(Contact, on_delete=models.CASCADE)
    # No per-field attribute set here; direction comes from
    # settings.BIDI_INPUT_OVERRIDES["testapp.Profile.bio"] instead.
    bio = models.TextField(blank=True)

    class Meta:
        app_label = "testapp"
