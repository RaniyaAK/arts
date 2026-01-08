from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.utils import timezone

from .models import User, Artwork
from .models import Commission


class RegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'Username', 'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Email', 'class': 'form-control'}),
            'password1': forms.PasswordInput(attrs={'placeholder': 'Password', 'class': 'form-control'}),
            'password2': forms.PasswordInput(attrs={'placeholder': 'Confirm Password', 'class': 'form-control'}),
        }


class LoginForm(forms.Form):
    username = forms.CharField(
        label="Username",
        widget=forms.TextInput(attrs={'placeholder': 'Username', 'class': 'form-control'})
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={'placeholder': 'Password', 'class': 'form-control'})
    )


class ForgotPasswordForm(forms.Form):
    email = forms.EmailField()


class ResetPasswordForm(forms.Form):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)


class ArtworkForm(forms.ModelForm):
    class Meta:
        model = Artwork
        fields = ['image']



class ProfileCompletionForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['name', 'bio', 'profile_image']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your Name'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Short bio', 'rows': 3}),
        }



class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['name', 'bio', 'profile_image']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your Name'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Short bio', 'rows': 3}),
        }


class CommissionRequestForm(forms.ModelForm):
    class Meta:
        model = Commission
        fields = ['title', 'description', 'reference_image', 'required_date']
        widgets = {
            'required_date': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control'}
            )
        }

class CommissionRequestForm(forms.ModelForm):
    class Meta:
        model = Commission
        fields = ['title', 'description', 'reference_image', 'required_date']
        widgets = {
            'required_date': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'form-control',
                }
            )
        }

    # ✅ FUTURE DATE VALIDATION
    def clean_required_date(self):
        required_date = self.cleaned_data.get('required_date')
        today = timezone.now().date()

        if required_date <= today:
            raise forms.ValidationError(
                "Required date must be a future date."
            )

        return required_date
    

class SetAdvanceAmountForm(forms.ModelForm):
    class Meta:
        model = Commission
        fields = ['advance_amount']
        widgets = {
            'advance_amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Advance ₹', 'min': 1})
        }
