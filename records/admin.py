from django.contrib import admin

from records.models import ClinicalScan, Patient


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ("last_name", "first_name", "sex", "birth_date", "age", "smoker", "diabetes")
    list_filter = ("sex", "smoker", "diabetes", "chemotherapy")
    search_fields = ("first_name", "last_name")


@admin.register(ClinicalScan)
class ClinicalScanAdmin(admin.ModelAdmin):
    list_display = ("patient", "modality", "performed_at", "diagnosis", "clinician")
    list_filter = ("modality", "performed_at")
    search_fields = ("patient__first_name", "patient__last_name", "reason", "diagnosis")
