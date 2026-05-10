from django import forms

from records.models import ClinicalScan, Patient


class DateInput(forms.DateInput):
    input_type = "date"


class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = [
            "first_name",
            "last_name",
            "birth_date",
            "sex",
            "weight_kg",
            "smoker",
            "pack_years",
            "diabetes",
            "insulin",
            "chemotherapy",
            "last_chemotherapy_date",
        ]
        widgets = {
            "birth_date": DateInput(),
            "last_chemotherapy_date": DateInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_bootstrap_classes(self.fields)


class ClinicalScanForm(forms.ModelForm):
    class Meta:
        model = ClinicalScan
        fields = ["performed_at", "modality", "reason", "diagnosis", "image"]
        widgets = {
            "performed_at": DateInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_bootstrap_classes(self.fields)


def apply_bootstrap_classes(fields):
    for field in fields.values():
        widget = field.widget
        if isinstance(widget, forms.CheckboxInput):
            widget.attrs["class"] = "form-check-input"
        elif isinstance(widget, forms.Select):
            widget.attrs["class"] = "form-select"
        else:
            widget.attrs["class"] = "form-control"
