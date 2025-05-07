from django import template

register = template.Library()

@register.filter
def has_profile(user):
    return hasattr(user, 'userprofile')

@register.filter
def is_owner(user):
    if hasattr(user, 'is_superuser') and user.is_superuser:
        return True
    try:
        return user.userprofile.role == 'owner'
    except Exception:
        return False

@register.filter
def is_receptionist(user):
    if hasattr(user, 'is_superuser') and user.is_superuser:
        return True # Superusers are implicitly all roles
    try:
        return user.userprofile.role in ['receptionist', 'owner']
    except UserProfile.DoesNotExist:
        return False
    except AttributeError: 
        return False

@register.filter
def is_lab_tech(user):
    if hasattr(user, 'is_superuser') and user.is_superuser:
        return True # Superusers are implicitly all roles
    try:
        return user.userprofile.role in ['lab_tech', 'owner']
    except UserProfile.DoesNotExist:
        return False
    except AttributeError: 
        return False 