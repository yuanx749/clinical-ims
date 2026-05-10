from datetime import date
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from PIL import Image

from records.models import ClinicalScan, Patient


class RecordsTestCase(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="docy", password="V7qN4pX9rL2m")
        self.patient = Patient.objects.create(
            first_name="Ava",
            last_name="Martin",
            birth_date=date(1980, 1, 1),
            sex=Patient.Sex.FEMALE,
            created_by=self.user,
        )

    def image_upload(self, name="scan.png"):
        image = Image.new("RGB", (24, 24), color="gray")
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/png")

    def create_scan(self, clinician=None):
        scan = ClinicalScan(
            patient=self.patient,
            clinician=clinician or self.user,
            performed_at=date(2025, 1, 10),
            modality=ClinicalScan.Modality.CT,
            reason="Follow-up examination",
            diagnosis="Normal finding",
            image=self.image_upload(),
        )
        scan.full_clean()
        scan.save()
        return scan

    def test_patient_age_uses_birth_date(self):
        patient = Patient(first_name="Test", last_name="User", birth_date=date(2000, 1, 1), sex=Patient.Sex.MALE)
        self.assertGreaterEqual(patient.age, 25)

    def test_patient_rejects_invalid_name_and_future_birth_date(self):
        patient = Patient(first_name="Ava1", last_name="Martin", birth_date=date(2099, 1, 1), sex=Patient.Sex.FEMALE)
        with self.assertRaises(ValidationError):
            patient.full_clean()

    def test_patient_rejects_unrealistic_weight(self):
        patient = Patient(
            first_name="Ava",
            last_name="Martin",
            birth_date=date(1980, 1, 1),
            sex=Patient.Sex.FEMALE,
            weight_kg=500,
        )
        with self.assertRaises(ValidationError):
            patient.full_clean()

    def test_scan_rejects_date_before_patient_birth(self):
        scan = ClinicalScan(
            patient=self.patient,
            clinician=self.user,
            performed_at=date(1979, 1, 1),
            modality=ClinicalScan.Modality.CT,
            reason="Follow-up examination",
            diagnosis="Normal finding",
            image=self.image_upload(),
        )
        with self.assertRaises(ValidationError):
            scan.full_clean()

    def test_authenticated_user_can_create_patient(self):
        self.client.login(username="docy", password="V7qN4pX9rL2m")
        response = self.client.post(
            reverse("patient_create"),
            {
                "first_name": "Liam",
                "last_name": "Stone",
                "birth_date": "1974-03-02",
                "sex": Patient.Sex.MALE,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Patient.objects.filter(first_name="Liam", last_name="Stone").exists())

    def test_patient_list_requires_login(self):
        response = self.client.get(reverse("patient_list"))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response["Location"].startswith("/login/"))

    def test_create_scan_binds_current_user(self):
        self.client.login(username="docy", password="V7qN4pX9rL2m")
        response = self.client.post(
            reverse("scan_create", args=[self.patient.id]),
            {
                "performed_at": "2025-01-10",
                "modality": ClinicalScan.Modality.CT,
                "reason": "Follow-up examination",
                "diagnosis": "Normal finding",
                "image": self.image_upload(),
            },
        )
        self.assertEqual(response.status_code, 302)
        scan = ClinicalScan.objects.get(patient=self.patient)
        self.assertEqual(scan.clinician, self.user)

    def test_create_scan_rejects_disguised_non_image_upload(self):
        self.client.login(username="docy", password="V7qN4pX9rL2m")
        fake_image = SimpleUploadedFile("scan.jpg", b"%PDF-1.4 not an image", content_type="image/jpeg")
        response = self.client.post(
            reverse("scan_create", args=[self.patient.id]),
            {
                "performed_at": "2025-01-10",
                "modality": ClinicalScan.Modality.CT,
                "reason": "Follow-up examination",
                "diagnosis": "Normal finding",
                "image": fake_image,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(ClinicalScan.objects.exists())

    def test_other_user_cannot_edit_scan(self):
        scan = self.create_scan()
        other_user = get_user_model().objects.create_user(username="other", password="V7qN4pX9rL2m")
        self.client.force_login(other_user)
        response = self.client.get(reverse("scan_update", args=[scan.id]))
        self.assertEqual(response.status_code, 403)

    def test_non_staff_user_cannot_delete_patient(self):
        self.client.login(username="docy", password="V7qN4pX9rL2m")
        response = self.client.get(reverse("patient_delete", args=[self.patient.id]))
        self.assertEqual(response.status_code, 403)

    def test_analytics_endpoint_returns_patient_records(self):
        self.create_scan()
        self.client.login(username="docy", password="V7qN4pX9rL2m")
        response = self.client.get(reverse("age_distribution_data"))
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload["records"]), 1)
        self.assertEqual(payload["records"][0]["sex"], Patient.Sex.FEMALE)
