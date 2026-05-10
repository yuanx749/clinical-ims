from datetime import date, timedelta
from decimal import Decimal
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from PIL import Image, ImageDraw

from records.models import ClinicalScan, Patient


class Command(BaseCommand):
    help = "Creates a sample clinician account and generated clinical records."

    def handle(self, *args, **options):
        if Patient.objects.exists():
            raise CommandError("Patients already exist. This command does not modify existing records.")

        clinician = self.create_sample_clinician()
        patients = self.create_patients(clinician)
        scans = self.create_scans(patients, clinician)

        self.stdout.write(self.style.SUCCESS(f"Created {len(patients)} patients and {len(scans)} scans."))
        self.stdout.write("Sample login: docy / V7qN4pX9rL2m")

    def create_sample_clinician(self):
        user_model = get_user_model()
        clinician, created = user_model.objects.get_or_create(
            username="docy",
            defaults={
                "email": "docy@example.test",
                "is_staff": True,
            },
        )
        if created:
            clinician.set_password("V7qN4pX9rL2m")
            clinician.save()
        return clinician

    def create_patients(self, clinician):
        names = [
            ("Ava", "Martin", Patient.Sex.FEMALE, date(1972, 4, 12), 68.5, True, 22.0, False, False, False),
            ("Liam", "Stone", Patient.Sex.MALE, date(1965, 9, 3), 81.0, True, 35.0, True, False, False),
            ("Mia", "Baker", Patient.Sex.FEMALE, date(1984, 1, 24), 59.2, False, None, False, False, True),
            ("Noah", "Clark", Patient.Sex.MALE, date(1958, 11, 18), 90.1, True, 40.0, True, True, False),
            ("Emma", "Davis", Patient.Sex.FEMALE, date(1991, 7, 7), 63.4, False, None, False, False, False),
            ("Oliver", "Reed", Patient.Sex.MALE, date(1978, 3, 29), 75.9, False, None, False, False, True),
            ("Sophia", "Hill", Patient.Sex.FEMALE, date(1949, 6, 15), 57.8, True, 18.5, True, True, False),
            ("James", "Ward", Patient.Sex.MALE, date(1989, 12, 2), 84.3, False, None, False, False, False),
            ("Isla", "Moore", Patient.Sex.FEMALE, date(1970, 8, 20), 70.0, True, 28.0, False, False, True),
            ("Henry", "King", Patient.Sex.MALE, date(1961, 5, 5), 78.6, True, 31.0, True, False, False),
            ("Grace", "Young", Patient.Sex.FEMALE, date(1996, 10, 11), 55.5, False, None, False, False, False),
            ("Lucas", "Scott", Patient.Sex.MALE, date(1982, 2, 16), 88.0, False, None, False, False, False),
        ]

        patients = []
        for first_name, last_name, sex, birth_date, weight, smoker, pack_years, diabetes, insulin, chemo in names:
            patients.append(
                Patient.objects.create(
                    first_name=first_name,
                    last_name=last_name,
                    birth_date=birth_date,
                    sex=sex,
                    weight_kg=Decimal(str(weight)),
                    smoker=smoker,
                    pack_years=Decimal(str(pack_years)) if pack_years else None,
                    diabetes=diabetes,
                    insulin=insulin,
                    chemotherapy=chemo,
                    last_chemotherapy_date=date(2025, 2, 10) if chemo else None,
                    created_by=clinician,
                )
            )
        return patients

    def create_scans(self, patients, clinician):
        modalities = [ClinicalScan.Modality.CT, ClinicalScan.Modality.XRAY, ClinicalScan.Modality.MRI, ClinicalScan.Modality.ULTRASOUND]
        reasons = [
            "Initial examination",
            "Follow-up examination",
            "Post-treatment review",
            "Routine surveillance",
        ]
        diagnoses = [
            "Normal finding",
            "Inflammatory change",
            "Benign lesion",
            "Follow-up recommended",
        ]

        scans = []
        for index, patient in enumerate(patients):
            scan_count = 1 + (index % 3)
            for offset in range(scan_count):
                modality = modalities[(index + offset) % len(modalities)]
                scan = ClinicalScan(
                    patient=patient,
                    clinician=clinician,
                    performed_at=date.today() - timedelta(days=30 * (offset + 1) + index),
                    modality=modality,
                    reason=reasons[(index + offset) % len(reasons)],
                    diagnosis=diagnoses[index % len(diagnoses)],
                )
                image = self.build_scan_image(index, offset)
                scan.image.save(f"sample-{patient.id}-{offset}.png", image, save=False)
                scan.full_clean()
                scan.save()
                scans.append(scan)
        return scans

    def build_scan_image(self, index, offset):
        image = Image.new("L", (640, 420), color=26)
        draw = ImageDraw.Draw(image)
        draw.rectangle((24, 24, 616, 396), outline=120, width=2)
        draw.ellipse((140 + offset * 18, 70, 500 - offset * 12, 350), outline=160, width=3)
        draw.line((80, 210 + index % 30, 560, 210 - index % 25), fill=95, width=2)

        buffer = BytesIO()
        image.save(buffer, format="PNG")
        return ContentFile(buffer.getvalue())
