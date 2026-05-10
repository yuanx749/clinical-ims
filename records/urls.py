from django.urls import path

from records import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("analytics/", views.analytics, name="analytics"),
    path("analytics/age-distribution/", views.age_distribution_data, name="age_distribution_data"),
    path("patients/", views.patient_list, name="patient_list"),
    path("patients/add/", views.patient_create, name="patient_create"),
    path("patients/<int:patient_id>/", views.patient_detail, name="patient_detail"),
    path("patients/<int:patient_id>/edit/", views.patient_update, name="patient_update"),
    path("patients/<int:patient_id>/delete/", views.patient_delete, name="patient_delete"),
    path("patients/<int:patient_id>/scans/add/", views.scan_create, name="scan_create"),
    path("scans/<int:scan_id>/", views.scan_detail, name="scan_detail"),
    path("scans/<int:scan_id>/edit/", views.scan_update, name="scan_update"),
    path("scans/<int:scan_id>/delete/", views.scan_delete, name="scan_delete"),
]
