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