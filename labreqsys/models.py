from django.db import models

class Patient(models.Model):
    patient_id = models.AutoField(primary_key=True)
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
    field_fixed_value = models.JSONField(blank=True, null=True)

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