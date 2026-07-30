from django import forms

from .models import ContactMessage


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ["name", "email", "subject", "message"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Your name", "class": "form-input"}),
            "email": forms.EmailInput(attrs={"placeholder": "you@example.com", "class": "form-input"}),
            "subject": forms.TextInput(attrs={"placeholder": "What's this about?", "class": "form-input"}),
            "message": forms.Textarea(attrs={"placeholder": "Tell me about your project...", "class": "form-input", "rows": 6}),
        }
