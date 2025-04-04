from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q


User = get_user_model()

class EmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # Try to find the user by their email address
            user = User.objects.get(Q(username=username) | Q(email=username))
        except User.DoesNotExist:
            # No user found, return None (authentication failed)
            return None
        else:
            # Check the password against the user's password
            if user.check_password(password):
                return user
        # Password didn't match, return None (authentication failed)
        return None
    