from django import template

register = template.Library()

@register.filter
def has_profile(user):
    return hasattr(user, 'userprofile')

@register.filter
def is_owner(user):
    if hasattr(user, 'is_superuser') and user.is_superuser:
        return True # Superusers are always considered owners
    try:
        # Check profile exists AND role is owner
        return hasattr(user, 'userprofile') and user.userprofile.role == 'owner'
    except (UserProfile.DoesNotExist, AttributeError):
        # Specifically catch profile not existing or attribute error
        return False
    except Exception as e:
        # Log other unexpected errors if necessary, but return False for safety
        print(f"Unexpected error in is_owner tag for user {user.username}: {e}") # Optional logging
        return False

@register.filter
def is_receptionist(user):
    if hasattr(user, 'is_superuser') and user.is_superuser:
        return True # Superusers are implicitly all roles
    try:
        return hasattr(user, 'userprofile') and user.userprofile.role in ['receptionist', 'owner']
    except (UserProfile.DoesNotExist, AttributeError):
        return False
    except Exception as e:
        print(f"Unexpected error in is_receptionist tag for user {user.username}: {e}") # Optional logging
        return False

@register.filter
def is_lab_tech(user):
    if hasattr(user, 'is_superuser') and user.is_superuser:
        return True # Superusers are implicitly all roles
    try:
        return hasattr(user, 'userprofile') and user.userprofile.role in ['lab_tech', 'owner']
    except (UserProfile.DoesNotExist, AttributeError):
        return False
    except Exception as e:
        print(f"Unexpected error in is_lab_tech tag for user {user.username}: {e}") # Optional logging
        return False 