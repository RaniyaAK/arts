from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from .forms import RegisterForm, LoginForm, ForgotPasswordForm, ResetPasswordForm
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from django.contrib.auth.decorators import login_required
from .forms import ArtworkForm
from .models import Artwork
from django.http import HttpResponseForbidden



User = get_user_model()

def home(request):
    return render(request,'home.html')

from django.contrib.auth import logout

def logout_view(request):
    logout(request)
    messages.success(request, "Logged out successfully")
    return redirect('login')


@login_required
def artist_dashboard(request):
    if request.user.role != 'artist':
        return redirect('login')

    artworks = Artwork.objects.filter(artist=request.user).order_by('-created_at')

    return render(request, 'dashboards/artist_dashboard.html', {
        'artworks': artworks,
        'numbers': range(1, 4),
    })



@login_required
def client_dashboard(request):
    if request.user.role != 'client':
        return redirect('login')
    return render(request, 'dashboards/client_dashboard.html')


def register_view(request):
    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()        
        login(request, user)     
        if user.role == 'artist':
            return redirect('artist_dashboard')
        elif user.role == 'client':
            return redirect('client_dashboard')

    return render(request, 'register.html', {'form': form})


def login_view(request):
    form = LoginForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        user = authenticate(
            request,
            username=form.cleaned_data['username'],
            password=form.cleaned_data['password']
        )

        if user is not None:
            login(request, user)

            # ✅ ROLE BASED REDIRECT
            if user.role == 'artist':
                return redirect('artist_dashboard')
            elif user.role == 'client':
                return redirect('client_dashboard')
            else:
                messages.error(request, "User role not assigned")
                return redirect('login')

        messages.error(request, "Invalid credentials")

    return render(request, 'login.html', {'form': form})


def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            return redirect('reset_password', email=user.email)
        except User.DoesNotExist:
            messages.error(request, 'No account found')
    return render(request, 'forgot_password.html')


def reset_password(request, email):
    if request.method == 'POST':
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
        else:
            try:
                user = User.objects.get(email=email)
                user.set_password(password)
                user.save()

                login(request, user)

                if user.role == 'artist':
                    return redirect('artist_dashboard')
                elif user.role == 'client':
                    return redirect('client_dashboard')

            except User.DoesNotExist:
                messages.error(request, 'Invalid user.')

    return render(request, 'reset_password.html')



@login_required
def add_artworks(request):
    if request.method == 'POST':
        form = ArtworkForm(request.POST, request.FILES)
        if form.is_valid():
            artwork = form.save(commit=False)
            artwork.artist = request.user
            artwork.save()
            return redirect('artist_dashboard')  # redirect to dashboard after submit
    else:
        form = ArtworkForm()

    return render(request, 'artist_dashboard/add_artworks.html', {'form': form})


def view_artworks(request):
    artworks = Artwork.objects.all().order_by('-created_at')
    return render(request, 'artist_dashboard/artworks.html', {
        'artworks': artworks
    })


def artwork_detail(request, artwork_id):
    artwork = Artwork.objects.get(id=artwork_id)
    return render(request, 'artist_dashboard/artwork_detail.html', {'artwork': artwork})


def edit_artwork(request, artwork_id):
    artwork = Artwork.objects.get(id=artwork_id)
    if request.user != artwork.artist:
        return HttpResponseForbidden()

    # form handling here
    if request.method == 'POST':
        form = ArtworkForm(request.POST, request.FILES, instance=artwork)
        if form.is_valid():
            form.save()
            return redirect('artwork_detail', artwork_id=artwork.id)
    else:
        form = ArtworkForm(instance=artwork)

    return render(request, 'edit_artwork.html', {'form': form})
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseForbidden
from .models import Artwork

def delete_artwork(request, artwork_id):
    # Get the artwork or 404
    artwork = get_object_or_404(Artwork, id=artwork_id)

    # Only the artist who owns it can delete
    if request.user != artwork.artist:
        return HttpResponseForbidden("You are not allowed to delete this artwork.")

    # Confirm deletion on POST
    if request.method == 'POST':
        artwork.delete()
        return redirect('artworks')  # Redirect to gallery page after delete

    # Render a simple confirmation page
    return render(request, 'artist_dashboard/delete_artwork.html', {'artwork': artwork})
