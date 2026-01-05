from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model
from .forms import RegisterForm, LoginForm, ForgotPasswordForm, ResetPasswordForm
from .forms import ArtworkForm, ProfileCompletionForm  # <-- new form
from .models import Artwork, Activity
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.views.decorators.cache import never_cache

User = get_user_model()


def home(request):
    return render(request, 'home.html')


# -------------------------------
# Profile Completion
# -------------------------------
@login_required
def complete_profile(request):
    if request.user.is_profile_complete:
        if request.user.role == 'artist':
            return redirect('artist_dashboard')
        else:
            return redirect('client_dashboard')

    if request.method == 'POST':
        form = ProfileCompletionForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_profile_complete = True
            user.save()
            if user.role == 'artist':
                return redirect('artist_dashboard')
            else:
                return redirect('client_dashboard')
    else:
        form = ProfileCompletionForm(instance=request.user)

    return render(request, 'complete_profile.html', {'form': form})


def register_view(request):
    if request.user.is_authenticated:
        # Already logged in users go straight to dashboard
        if request.user.role == 'artist':
            return redirect('artist_dashboard')
        elif request.user.role == 'client':
            return redirect('client_dashboard')

    form = RegisterForm(request.POST or None)
    role = request.POST.get('role') or request.GET.get('role')

    if request.method == 'POST' and form.is_valid():
        user = form.save(commit=False)

        if role not in ['artist', 'client']:
            return render(request, 'register.html', {'form': form, 'role': role})

        user.role = role
        user.is_profile_complete = False  # ✅ profile not complete yet
        user.save()

        login(request, user)  # automatically log in after registration

        # Redirect **immediately to profile completion**
        return redirect('complete_profile')

    return render(request, 'register.html', {'form': form, 'role': role})

def login_view(request):
    if request.user.is_authenticated:
        # Normal login, go straight to dashboard
        if request.user.role == 'artist':
            return redirect('artist_dashboard')
        elif request.user.role == 'client':
            return redirect('client_dashboard')

    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # No profile check here — only after registration
            if user.role == 'artist':
                return redirect('artist_dashboard')
            elif user.role == 'client':
                return redirect('client_dashboard')

    return render(request, 'login.html', {'form': form})


# Logout View
@login_required
def logout_view(request):
    logout(request)
    return redirect('login')


# Forgot & Reset Password
def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            return redirect('reset_password', email=user.email)
        except User.DoesNotExist:
            pass
    return render(request, 'forgot_password.html')


def reset_password(request, email):
    if request.method == 'POST':
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        if password == confirm_password:
            try:
                user = User.objects.get(email=email)
                user.set_password(password)
                user.save()
                login(request, user)
                if not user.is_profile_complete:
                    return redirect('complete_profile')
                if user.role == 'artist':
                    return redirect('artist_dashboard')
                elif user.role == 'client':
                    return redirect('client_dashboard')
            except User.DoesNotExist:
                pass
    return render(request, 'reset_password.html')


# -------------------------------
# Artwork Views (unchanged)
# -------------------------------
@login_required
def artist_dashboard(request):
    if request.user.role != 'artist':
        return redirect('login')

    artworks = Artwork.objects.filter(artist=request.user).order_by('-created_at')
    activities = Activity.objects.filter(user=request.user).order_by('-created_at')[:10]

    return render(request, 'dashboards/artist_dashboard.html', {
        'artworks': artworks,
        'activities': activities,
        'numbers': range(1, 4),
    })


@login_required
def client_dashboard(request):
    if request.user.role != 'client':
        return redirect('login')
    if not request.user.is_profile_complete:
        return redirect('complete_profile')

    artworks = Artwork.objects.all().order_by('-created_at')[:6]
    featured_artists = User.objects.filter(role='artist')
    return render(request, 'dashboards/client_dashboard.html', {'artworks': artworks, 'featured_artists': featured_artists})

@login_required
def add_artworks(request):
    if request.method == 'POST':
        form = ArtworkForm(request.POST, request.FILES)
        if form.is_valid():
            artwork = form.save(commit=False)
            artwork.artist = request.user
            artwork.save()
            Activity.objects.create(user=request.user, artwork_title=artwork.title, action='added')
            return redirect('artist_dashboard')
    else:
        form = ArtworkForm()
    return render(request, 'artist_dashboard/add_artworks.html', {'form': form})
