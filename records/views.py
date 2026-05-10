from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from records.forms import ClinicalScanForm, PatientForm
from records.models import ClinicalScan, Patient


@login_required
def dashboard(request):
    context = {
        "patient_count": Patient.objects.count(),
        "scan_count": ClinicalScan.objects.count(),
        "clinician_count": get_user_model().objects.count(),
    }
    return render(request, "records/dashboard.html", context)


@login_required
def analytics(request):
    return render(
        request,
        "records/analytics.html",
        {
            "sex_choices": Patient.Sex.choices,
        },
    )


@login_required
def age_distribution_data(request):
    records = []
    patients = Patient.objects.prefetch_related("scans")
    for patient in patients:
        records.append(
            {
                "id": patient.id,
                "age": patient.age,
                "sex": patient.sex,
            }
        )
    return JsonResponse({"records": records})


@login_required
def patient_list(request):
    search = request.GET.get("q", "").strip()
    patients = Patient.objects.all()
    if search:
        patients = patients.filter(Q(first_name__icontains=search) | Q(last_name__icontains=search))
    return render(request, "records/patient_list.html", {"patients": patients, "search": search})


@login_required
def patient_detail(request, patient_id):
    patient = get_object_or_404(Patient, pk=patient_id)
    return render(request, "records/patient_detail.html", {"patient": patient})


@login_required
def patient_create(request):
    if request.method == "POST":
        form = PatientForm(request.POST)
        if form.is_valid():
            patient = form.save(commit=False)
            patient.created_by = request.user
            patient.save()
            messages.success(request, "Patient created.")
            return redirect("patient_detail", patient_id=patient.id)
    else:
        form = PatientForm()
    return render(request, "records/patient_form.html", {"form": form, "title": "Add patient"})


@login_required
def patient_update(request, patient_id):
    patient = get_object_or_404(Patient, pk=patient_id)
    if request.method == "POST":
        form = PatientForm(request.POST, instance=patient)
        if form.is_valid():
            form.save()
            messages.success(request, "Patient updated.")
            return redirect("patient_detail", patient_id=patient.id)
    else:
        form = PatientForm(instance=patient)
    return render(request, "records/patient_form.html", {"form": form, "title": "Edit patient", "patient": patient})


@login_required
def patient_delete(request, patient_id):
    if not request.user.is_staff:
        raise PermissionDenied
    patient = get_object_or_404(Patient, pk=patient_id)
    if request.method == "POST":
        for scan in patient.scans.all():
            scan.image.delete(save=False)
        patient.delete()
        messages.success(request, "Patient deleted.")
        return redirect("patient_list")
    return render(request, "records/confirm_delete.html", {"object": patient, "cancel_url": reverse("patient_detail", args=[patient.id])})


@login_required
def scan_create(request, patient_id):
    patient = get_object_or_404(Patient, pk=patient_id)
    if request.method == "POST":
        form = ClinicalScanForm(request.POST, request.FILES)
        if form.is_valid():
            scan = form.save(commit=False)
            scan.patient = patient
            scan.clinician = request.user
            try:
                scan.full_clean()
            except ValidationError as error:
                form.add_error(None, error)
            else:
                scan.save()
                messages.success(request, "Scan created.")
                return redirect("patient_detail", patient_id=patient.id)
    else:
        form = ClinicalScanForm()
    return render(request, "records/scan_form.html", {"form": form, "patient": patient, "title": "Add scan"})


@login_required
def scan_detail(request, scan_id):
    scan = get_object_or_404(ClinicalScan, pk=scan_id)
    return render(request, "records/scan_detail.html", {"scan": scan})


@login_required
def scan_update(request, scan_id):
    scan = get_object_or_404(ClinicalScan, pk=scan_id)
    if scan.clinician != request.user:
        raise PermissionDenied
    if request.method == "POST":
        form = ClinicalScanForm(request.POST, request.FILES, instance=scan)
        if form.is_valid():
            form.save()
            messages.success(request, "Scan updated.")
            return redirect("scan_detail", scan_id=scan.id)
    else:
        form = ClinicalScanForm(instance=scan)
    return render(request, "records/scan_form.html", {"form": form, "patient": scan.patient, "scan": scan, "title": "Edit scan"})


@login_required
def scan_delete(request, scan_id):
    scan = get_object_or_404(ClinicalScan, pk=scan_id)
    if scan.clinician != request.user:
        raise PermissionDenied
    patient_id = scan.patient_id
    if request.method == "POST":
        scan.image.delete(save=False)
        scan.delete()
        messages.success(request, "Scan deleted.")
        return redirect("patient_detail", patient_id=patient_id)
    return render(request, "records/confirm_delete.html", {"object": scan, "cancel_url": reverse("scan_detail", args=[scan.id])})
