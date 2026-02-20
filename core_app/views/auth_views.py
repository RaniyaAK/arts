from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.decorators import login_required

from ..forms import RegisterForm, LoginForm, ForgotPasswordForm, ResetPasswordForm

from ..models import Notification

User = get_user_model()



def register_view(request):
    if request.user.is_authenticated:
        if request.user.role == 'artist':
            return redirect('artist_dashboard')
        elif request.user.role == 'client':
            return redirect('client_dashboard')

    form = RegisterForm(request.POST or None)
    role = request.POST.get('role') or request.GET.get('role')

    if request.method == 'POST' and form.is_valid():
        user = form.save(commit=False)

        if role not in ['artist', 'client']:
            return render(request, 'auth/register.html', {'form': form, 'role': role})

        user.role = role
        user.is_profile_complete = False

        if user.role == "artist":
            user.is_approved = False   
        else:
            user.is_approved = True   

        user.save()

        if user.role == "artist":
            admin_user = User.objects.filter(is_superuser=True).first()
            if admin_user:
                Notification.objects.create(
                    receiver=admin_user,
                    message=f"New artist registered: {user.name}",
                    notification_type="new_artist"
                )

        if user.role == "artist":
            messages.info(request, "Your registration is submitted. Please wait for admin approval.")
            return redirect("login")

        login(request, user)
        return redirect('complete_profile')

    return render(request, 'auth/register.html', {'form': form, 'role': role})



def login_view(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect("admin_dashboard")
        elif request.user.role == "artist":
            return redirect("artist_dashboard")
        elif request.user.role == "client":
            return redirect("client_dashboard")

    form = LoginForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']

        user = authenticate(request, username=username, password=password)

        if user is not None:

            if user.role == "artist" and not user.is_approved:
                messages.error(request, "Your artist account is not yet approved by admin.")
                return redirect('login')

            login(request, user)

            if user.is_superuser:
                return redirect("admin_dashboard")

            if user.role == "artist":
                if not user.is_profile_complete:
                    return redirect("complete_profile")
                return redirect("artist_dashboard")


            if user.role == 'client':
                return redirect('client_dashboard')

        else:
            messages.error(request, "Invalid username or password.")

    return render(request, 'auth/login.html', {'form': form})



# Logout View
@login_required
def logout_view(request):
    logout(request)
    return redirect('login')



def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        user = User.objects.filter(email=email).first()

        if not user:
            messages.error(request, "No account found with this email.")
            return redirect('forgot_password')

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        reset_link = request.build_absolute_uri(
            f"/reset-password/{uid}/{token}/"
        )

        send_mail(
            subject="Reset Your Password - Paletra",
            message=f"Click the link to reset your password:\n\n{reset_link}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
        )

        messages.success(request, "Password reset link sent to your email.")
        return redirect('login')

    return render(request, 'auth/forgot_password.html')

def reset_password(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except:
        user = None

    if user is None or not default_token_generator.check_token(user, token):
        messages.error(request, "Invalid or expired reset link.")
        return redirect('forgot_password')

    if request.method == 'POST':
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect(request.path)

        if len(password) < 6:
            messages.error(request, "Password must be at least 6 characters.")
            return redirect(request.path)

        user.set_password(password)
        user.save()

        return redirect('password_reset_success')

    return render(request, 'auth/reset_password.html')



def password_reset_success(request):
    return render(request, 'auth/password_reset_success.html')


def password_reset_sent(request):
    return render(request, 'auth/password_reset_sent.html')