import uuid
from datetime import date

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator, MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver


def validate_past_date(value):
    if value > date.today():
        raise ValidationError("Date cannot be in the future.")


def validate_scan_image_size(value):
    max_size = 2 * 1024 * 1024
    if value.size > max_size:
        raise ValidationError("Image size cannot exceed 2 MB.")


def scan_upload_path(instance, filename):
    extension = filename.rsplit(".", 1)[-1].lower()
    return f"scans/{uuid.uuid4().hex}.{extension}"


class Patient(models.Model):
    class Sex(models.TextChoices):
        FEMALE = "F", "Female"
        MALE = "M", "Male"

    name_validator = RegexValidator(
        regex=r"^[A-Za-z][A-Za-z -]*$",
        message="Use letters, spaces, or hyphens only.",
    )

    first_name = models.CharField(max_length=40, validators=[name_validator])
    last_name = models.CharField(max_length=40, validators=[name_validator])
    birth_date = models.DateField(
        validators=[
            MinValueValidator(date(1900, 1, 1)),
            validate_past_date,
        ]
    )
    sex = models.CharField(max_length=1, choices=Sex.choices)
    weight_kg = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(300)],
    )
    smoker = models.BooleanField(default=False)
    pack_years = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    diabetes = models.BooleanField(default=False)
    insulin = models.BooleanField(default=False)
    chemotherapy = models.BooleanField(default=False)
    last_chemotherapy_date = models.DateField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="patients",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["last_name", "first_name", "birth_date"]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def age(self):
        today = date.today()
        had_birthday = (today.month, today.day) >= (self.birth_date.month, self.birth_date.day)
        return today.year - self.birth_date.year - (not had_birthday)

    def clean(self):
        if self.last_chemotherapy_date and self.last_chemotherapy_date < self.birth_date:
            raise ValidationError({"last_chemotherapy_date": "Date cannot be before birth date."})
        if self.last_chemotherapy_date and self.last_chemotherapy_date > date.today():
            raise ValidationError({"last_chemotherapy_date": "Date cannot be in the future."})
        if not self.smoker and self.pack_years:
            raise ValidationError({"pack_years": "Pack years should be empty for non-smokers."})
        if not self.diabetes and self.insulin:
            raise ValidationError({"insulin": "Insulin should be false when diabetes is false."})
        if not self.chemotherapy and self.last_chemotherapy_date:
            raise ValidationError({"last_chemotherapy_date": "Date should be empty when chemotherapy is false."})


class ClinicalScan(models.Model):
    class Modality(models.TextChoices):
        CT = "CT", "CT"
        MRI = "MRI", "MRI"
        XRAY = "XR", "X-ray"
        ULTRASOUND = "US", "Ultrasound"

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="scans")
    clinician = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="clinical_scans")
    performed_at = models.DateField(default=date.today, validators=[validate_past_date])
    modality = models.CharField(max_length=3, choices=Modality.choices)
    reason = models.CharField(max_length=120)
    diagnosis = models.CharField(max_length=120)
    image = models.ImageField(
        upload_to=scan_upload_path,
        validators=[
            FileExtensionValidator(["jpg", "jpeg", "png"]),
            validate_scan_image_size,
        ],
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-performed_at", "-created_at"]

    def __str__(self):
        return f"{self.get_modality_display()} scan for {self.patient} on {self.performed_at}"

    def clean(self):
        if self.patient_id and self.performed_at < self.patient.birth_date:
            raise ValidationError({"performed_at": "Scan date cannot be before patient birth date."})


@receiver(post_delete, sender=ClinicalScan)
def delete_scan_image(sender, instance, **kwargs):
    if instance.image:
        instance.image.delete(save=False)
