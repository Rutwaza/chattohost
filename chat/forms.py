# chat/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser
from django.conf import settings
        

class CustomUserCreationForm(UserCreationForm):
    secret_code = forms.CharField(max_length=50, required=True, help_text="Enter the secret code to join.")

    class Meta:
        model = CustomUser
        fields = ("username", "email", "phone", "password1", "password2")

    def clean_secret_code(self):
        code = self.cleaned_data.get("secret_code")
        if code != settings.SECRET_CHAT_CODE:
            raise forms.ValidationError("Wrong secret code! You cannot register without it.")
        return code

class SecretLoginForm(AuthenticationForm):
    secret_code = forms.CharField(max_length=50, required=True, help_text="Enter the secret code to login.")

    def clean(self):
        cleaned_data = super().clean()
        code = cleaned_data.get("secret_code")
        if code != settings.SECRET_CHAT_CODE:
            raise forms.ValidationError("Wrong secret code! Access denied.")
        return cleaned_data
