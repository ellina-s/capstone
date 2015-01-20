from django import forms

# A form for changing a password via a user profile.
class PasswordForm(forms.Form):
    old_password = forms.CharField(max_length=16,
	widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your current password' }))
    new_password = forms.CharField(max_length=32,
	widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter new password' }))
    confirm_new_password = forms.CharField(max_length=32,
	widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter new password again' }))
