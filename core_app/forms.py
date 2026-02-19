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
        fields = ['image', 'artwork_title']



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

    phone_number = forms.CharField(
        max_length=10,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter 10-digit phone number'
        })
    )


    delivery_address = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Enter delivery address',
            'rows': 3
        }),
        required=True           # <-- UPDATED (previously False)
    )

    delivery_latitude = forms.FloatField(
        widget=forms.HiddenInput(),
        required=False
    )

    delivery_longitude = forms.FloatField(
        widget=forms.HiddenInput(),
        required=False
    )

    class Meta:
        model = Commission
        fields = [
            'title',
            'description',
            'reference_image',
            'required_date',
            'phone_number',
            'delivery_address',
            'delivery_latitude',
            'delivery_longitude',
        ]
        widgets = {
            'required_date': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control'}
            )
        }

    def clean_phone_number(self):
        phone = self.cleaned_data.get("phone_number", "").strip()

        if not phone.isdigit():
            raise forms.ValidationError("Phone number must contain only digits.")

        if len(phone) != 10:
            raise forms.ValidationError("Phone number must be exactly 10 digits.")

        if phone[0] not in {'6', '7', '8', '9'}:
            raise forms.ValidationError("Phone number must start with 6, 7, 8, or 9.")

        return phone    

    def clean_required_date(self):
        required_date = self.cleaned_data.get('required_date')
        today = timezone.now().date()

        if required_date <= today:
            raise forms.ValidationError("Required date must be a future date.")
        return required_date



class SetTotalPriceForm(forms.ModelForm):
    class Meta:
        model = Commission
        fields = ['total_price']
        widgets = {
            'total_price': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Total price ₹',
                    'min': 1
                }
            )
        }

    def clean_total_price(self):
        price = self.cleaned_data.get('total_price')
        if price <= 0:
            raise forms.ValidationError("Total price must be greater than zero.")
        return price
