# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150)

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class AuthUser(models.Model):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.IntegerField()
    username = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.CharField(max_length=254)
    is_staff = models.IntegerField()
    is_active = models.IntegerField()
    date_joined = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'auth_user'


class AuthUserGroups(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_groups'
        unique_together = (('user', 'group'),)


class AuthUserUserPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_user_permissions'
        unique_together = (('user', 'permission'),)


class CollectionLog(models.Model):
    collection_id = models.AutoField(primary_key=True)
    request = models.ForeignKey('LabRequest', models.DO_NOTHING)
    collected_by_customer = models.CharField(max_length=100)
    time_collected = models.DateTimeField()
    mode_of_collection = models.CharField(max_length=7)

    class Meta:
        managed = False
        db_table = 'collection_log'


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.PositiveSmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    id = models.BigAutoField(primary_key=True)
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'


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


class Patient(models.Model):
    patient_id = models.AutoField(primary_key=True)
    last_name = models.CharField(max_length=50)
    first_name = models.CharField(max_length=50)
    middle_initial = models.CharField(max_length=1, blank=True, null=True)
    suffix = models.CharField(max_length=5, blank=True, null=True)
    sex = models.CharField(max_length=6)
    birthdate = models.DateField(blank=True, null=True)
    mobile_num = models.CharField(max_length=12, blank=True, null=True)
    landline_num = models.CharField(max_length=9, blank=True, null=True)
    pwd_id_num = models.CharField(max_length=20, blank=True, null=True)
    senior_id_num = models.CharField(max_length=20, blank=True, null=True)
    email = models.CharField(max_length=50, blank=True, null=True)
    house_num = models.CharField(max_length=10, blank=True, null=True)
    street = models.CharField(max_length=100, blank=True, null=True)
    subdivision = models.CharField(max_length=100, blank=True, null=True)
    baranggay = models.CharField(max_length=50, blank=True, null=True)
    city = models.CharField(max_length=50)
    province = models.CharField(max_length=50, blank=True, null=True)
    zip_code = models.CharField(max_length=4, blank=True, null=True)
    civil_status = models.CharField(max_length=7)
    date_added = models.DateField()

    class Meta:
        managed = False
        db_table = 'patient'


class RequestComponent(models.Model):
    id = models.BigAutoField(primary_key=True)
    component = models.ForeignKey('TestComponent', models.DO_NOTHING)
    request = models.ForeignKey(LabRequest, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'request_component'
        unique_together = (('request', 'component'),)


class RequestLineItem(models.Model):
    line_item_id = models.AutoField(primary_key=True)
    request_status = models.CharField(max_length=20)
    component = models.ForeignKey('TestComponent', models.DO_NOTHING)
    package = models.ForeignKey('TestPackage', models.DO_NOTHING, blank=True, null=True)
    request = models.ForeignKey(LabRequest, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'request_line_item'


class RequestPackage(models.Model):
    id = models.BigAutoField(primary_key=True)
    package = models.ForeignKey('TestPackage', models.DO_NOTHING)
    request = models.ForeignKey(LabRequest, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'request_package'
        unique_together = (('request', 'package'),)


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
