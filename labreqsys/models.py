from django.db import models
from django.contrib.auth.models import User
from datetime import timedelta, timezone

class Patient(models.Model):
    patient_id = models.AutoField(primary_key=True)
    last_name = models.CharField(max_length=50)
    first_name = models.CharField(max_length=50)
    middle_initial = models.CharField(max_length=1, blank=True, null=True)
    suffix = models.CharField(max_length=5, blank=True, null=True)
    sex = models.CharField(max_length=6)
    birthdate = models.DateField(blank=True, null=True)
    mobile_num = models.CharField(max_length=12, blank=True, null=True)
    landline_num = models.CharField(max_length=9,blank=True, null=True)
    pwd_id_num = models.CharField(max_length=20, blank=True, null=True)
    senior_id_num = models.CharField(max_length=20, blank=True, null=True)
    email = models.CharField(max_length=50,blank=True, null=True)
    house_num = models.CharField(max_length=10, blank=True, null=True)
    street = models.CharField(max_length=100, blank=True, null=True)
    subdivision = models.CharField(max_length=100, blank=True, null=True)
    baranggay = models.CharField(max_length=50, blank=True, null=True)
    city = models.CharField(max_length=50)
    province = models.CharField(max_length=50, blank=True, null=True)
    zip_code = models.CharField(max_length=4,blank=True, null=True)
    civil_status = models.CharField(max_length=7)
    date_added = models.DateField()

    class Meta:
        managed = False
        db_table = 'patient'

class LabRequest(models.Model):
    request_id = models.AutoField(primary_key=True)
    patient = models.ForeignKey('Patient', models.DO_NOTHING)
    date_requested = models.DateField()
    physician = models.CharField(max_length=100, blank=True, null=True)
    mode_of_release = models.CharField(max_length=7)
    overall_status = models.CharField(max_length=11)

    def get_request_details(self):
        # Get collection status based on mode_of_release
        collection_status = 'Uncollected'
        if self.mode_of_release == 'Pick-up':
            collection_logs = CollectionLog.objects.filter(request=self).order_by('-time_collected').first()
            if collection_logs:
                collection_status = 'Collected'
        
        # Get email status based on mode_of_release
        email_status = 'Not Sent'
        if self.mode_of_release in ['Email', 'Both']:
            # You can add email tracking logic here if needed
            email_status = 'Sent' if self.overall_status == 'Completed' else 'Not Sent'

        return {
            'request_id': self.request_id,
            'patient': self.patient,
            'date_requested': self.date_requested,
            'physician': self.physician,
            'mode_of_release': self.mode_of_release,
            'overall_status': self.overall_status,
            'collection_status': collection_status,
            'email_status': email_status,
            'components': self.requestcomponent_set.all(),
            'packages': self.requestpackage_set.all(),
            'line_items': self.requestlineitem_set.all()
        }

    class Meta:
        managed = False
        db_table = 'lab_request'

class CollectionLog(models.Model):
    collection_id = models.AutoField(primary_key=True)
    request = models.ForeignKey('LabRequest', models.DO_NOTHING)
    collected_by_customer = models.CharField(max_length=100)
    time_collected = models.DateTimeField()
    mode_of_collection = models.CharField(max_length=7)

    class Meta:
        managed = False
        db_table = 'collection_log'

class TemplateField(models.Model):
    field_id = models.AutoField(primary_key=True)
    section = models.ForeignKey('TemplateSection', models.DO_NOTHING)
    label_name = models.CharField(max_length=255)
    field_type = models.CharField(max_length=6)
    field_value = models.JSONField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'template_field'


class TemplateForm(models.Model):
    template_id = models.AutoField(primary_key=True)
    template_name = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'template_form'


class TemplateSection(models.Model):
    section_id = models.AutoField(primary_key=True)
    template = models.ForeignKey(TemplateForm, models.DO_NOTHING)
    section_name = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'template_section'


class TestComponent(models.Model):
    component_id = models.AutoField(primary_key=True)
    template = models.ForeignKey(TemplateForm, models.DO_NOTHING)
    test_code = models.CharField(max_length=20)
    test_name = models.CharField(max_length=100)
    component_price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'test_component'


class TestPackage(models.Model):
    package_id = models.AutoField(primary_key=True)
    package_name = models.CharField(max_length=100)
    package_price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        managed = False
        db_table = 'test_package'

class TestPackageComponent(models.Model):
    package = models.OneToOneField(TestPackage, models.DO_NOTHING, primary_key=True)  # The composite primary key (package_id, component_id) found, that is not supported. The first column is selected.
    component = models.ForeignKey(TestComponent, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'test_package_component'
        unique_together = (('package', 'component'),)

class RequestComponent(models.Model):
    id = models.BigAutoField(primary_key=True)
    component = models.ForeignKey(TestComponent, models.DO_NOTHING)
    request = models.ForeignKey(LabRequest, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'request_component'
        unique_together = (('request', 'component'),)

class RequestPackage(models.Model):
    id = models.BigAutoField(primary_key=True)
    package = models.ForeignKey(TestPackage, models.DO_NOTHING)
    request = models.ForeignKey(LabRequest, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'request_package'
        unique_together = (('request', 'package'),)

class RequestLineItem(models.Model):
    line_item_id = models.AutoField(primary_key=True)
    request_status = models.CharField(max_length=20)
    component = models.ForeignKey(TestComponent, models.DO_NOTHING)
    package = models.ForeignKey(TestPackage, models.DO_NOTHING, blank=True, null=True)
    request = models.ForeignKey(LabRequest, models.DO_NOTHING)
    template_used = models.IntegerField()
    progress_timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'request_line_item'

class ResultValue(models.Model):
    result_value_id = models.AutoField(primary_key=True)
    line_item = models.ForeignKey(RequestLineItem, models.DO_NOTHING)
    field = models.ForeignKey('TemplateField', models.DO_NOTHING)
    field_value = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'result_value'

class LabTech(models.Model):
    lab_tech_id = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, unique=True, null=True, blank=True)
    last_name = models.CharField(max_length=50)
    first_name = models.CharField(max_length=50)
    title = models.CharField(max_length=30)
    tech_role = models.CharField(max_length=30)
    license_num = models.CharField(max_length=50)
    signature_path = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'lab_tech'

class ResultReview(models.Model):
    lab_tech = models.OneToOneField(LabTech, models.DO_NOTHING, primary_key=True)  # The composite primary key (lab_tech_id, result_value_id) found, that is not supported. The first column is selected.
    line_item = models.ForeignKey(RequestLineItem, models.DO_NOTHING)
    reviewed_date = models.DateField()

    class Meta:
        managed = False
        db_table = 'result_review'
        unique_together = (('lab_tech', 'line_item'),)

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('owner', 'Owner'),
        ('receptionist', 'Receptionist'),
        ('lab_tech', 'Lab Technician'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"
    
class EditPatientPasscode (models.Model):
    patient_id = models.OneToOneField(Patient,on_delete=models.CASCADE)
    code = models.CharField(max_length=5)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=5)