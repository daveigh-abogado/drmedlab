from django.db import models

class Patients(models.Model):
    patient_id = models.CharField(primary_key=True, max_length=6)
    last_name = models.CharField(max_length=50)
    first_name = models.CharField(max_length=50)
    middle_initial = models.CharField(max_length=1, blank=True, null=True)
    suffix = models.CharField(max_length=5, blank=True, null=True)
    sex = models.CharField(max_length=6)
    birthdate = models.DateField(blank=True, null=True)
    mobile_num = models.JSONField(blank=True, null=True)
    landline_num = models.JSONField(blank=True, null=True)
    pwd_id_num = models.CharField(max_length=20, blank=True, null=True)
    senior_id_num = models.CharField(max_length=20, blank=True, null=True)
    email = models.JSONField(blank=True, null=True)
    house_num = models.CharField(max_length=10, blank=True, null=True)
    street = models.CharField(max_length=100, blank=True, null=True)
    subdivision = models.CharField(max_length=100, blank=True, null=True)
    baranggay = models.CharField(max_length=50, blank=True, null=True)
    city = models.CharField(max_length=50)
    province = models.CharField(max_length=50, blank=True, null=True)
    zip_code = models.JSONField(blank=True, null=True)
    civil_status = models.CharField(max_length=7)

    class Meta:
        managed = False
        db_table = 'patients'

class LabRequest(models.Model):
    request_id = models.CharField(primary_key=True, max_length=6)
    patient = models.ForeignKey('Patients', models.DO_NOTHING)
    date_requested = models.DateField()
    physician = models.CharField(max_length=100, blank=True, null=True)
    mode_of_release = models.CharField(max_length=7)
    overall_status = models.CharField(max_length=11)

    class Meta:
        managed = False
        db_table = 'lab_request'
