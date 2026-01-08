from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.views.decorators.cache import never_cache
from django.http import JsonResponse
from django.db.models import Q
from django.utils import timezone


from .forms import RegisterForm, LoginForm, ForgotPasswordForm, ResetPasswordForm
from .forms import ArtworkForm, ProfileCompletionForm 
from .forms import ProfileEditForm
from .forms import CommissionRequestForm

from .models import Artwork, Activity
from .models import Commission


User = get_user_model()


def home(request):
    return render(request, 'home.html')


# Profile Completion
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


def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        user = User.objects.filter(email=email).first()
        if not user:
            return render(request, 'forgot_password.html', {
                'error': 'Email not found'
            })

        return redirect('reset_password', email=user.email)

    return render(request, 'forgot_password.html')


def reset_password(request, email):
    user = User.objects.filter(email=email).first()
    if not user:
        return redirect('forgot_password')

    if request.method == 'POST':
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if password == confirm_password:
            user.set_password(password)
            user.save()
            login(request, user)

            if not user.is_profile_complete:
                return redirect('complete_profile')
            if user.role == 'artist':
                return redirect('artist_dashboard')
            elif user.role == 'client':
                return redirect('client_dashboard')

    return render(request, 'reset_password.html')

#  ________________________________________________________________________________________________________________________


# Artwork Views (unchanged)
@login_required
def artist_dashboard(request):
    if request.user.role != 'artist':
        return redirect('login')

    # Artist's own artworks
    artworks = Artwork.objects.filter(artist=request.user).order_by('-created_at')

    # Recent activities
    activities = Activity.objects.filter(user=request.user).order_by('-created_at')[:10]

    # 🔹 Commissions requested to this artist
    commissions = Commission.objects.filter(artist=request.user).order_by('-created_at')

    return render(request, 'dashboards/artist_dashboard.html', {
        'artworks': artworks,
        'activities': activities,
        'numbers': range(1, 4),
        'commissions': commissions,  # ✅ Pass commissions here
    })


@login_required
def client_dashboard(request):
    if request.user.role != 'client':
        return redirect('login')
    if not request.user.is_profile_complete:
        return redirect('complete_profile')

    # 🔍 Search logic
    search_query = request.GET.get('search', '')

    if search_query:
        featured_artists = User.objects.filter(
            role='artist',
            name__icontains=search_query
        )
    else:
        featured_artists = User.objects.filter(role='artist')

    artworks = Artwork.objects.all().order_by('-created_at')[:6]

    return render(
        request,
        'dashboards/client_dashboard.html',
        {
            'artworks': artworks,
            'featured_artists': featured_artists
        }
    )

# ____________________________________________________________________________________________________________________


@login_required
def edit_profile(request):
    user = request.user
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            return redirect('artist_dashboard' if user.role=='artist' else 'client_dashboard')
    else:
        form = ProfileEditForm(instance=user)

    return render(request, 'edit_profile.html', {'form': form})


# __________________________________________________________________________________________________________________________


@login_required
def add_artworks(request):
    if request.method == 'POST':
        form = ArtworkForm(request.POST, request.FILES)
        if form.is_valid():
            artwork = form.save(commit=False)
            artwork.artist = request.user
            artwork.save()

            Activity.objects.create(
                user=request.user,
                artwork_title='Sample Artwork',
                action='added'
            )

            return redirect('artist_dashboard')
    else:
        form = ArtworkForm()

    return render(request, 'artist_dashboard/add_artworks.html', {'form': form})

@login_required
def delete_artwork(request, artwork_id):
    artwork = get_object_or_404(Artwork, id=artwork_id, artist=request.user)

    if request.method == 'POST':
        artwork.delete()
        return redirect('artist_dashboard')

    return render(request, 'artist_dashboard/delete_artwork.html', {
        'artwork': artwork
    })

# ________________________________________________________________________________________________________________________


@login_required
def all_artworks(request):
    if request.user.role != 'client':
        return redirect('login')

    artworks = Artwork.objects.all().order_by('-created_at')
    return render(request, 'client_dashboard/all_artworks.html', {'artworks': artworks})


def artist_profile(request, artist_id):
    artist = get_object_or_404(User, id=artist_id, role='artist')
    artworks = Artwork.objects.filter(artist=artist)

    return render(request, 'artist_dashboard/artist_profile.html', {
        'artist': artist,
        'artworks': artworks,
    })



@login_required
def request_commission(request, artist_id):
    artist = get_object_or_404(User, id=artist_id)

    if request.method == 'POST':
        form = CommissionRequestForm(request.POST, request.FILES)
        if form.is_valid():
            commission = form.save(commit=False)
            commission.client = request.user
            commission.artist = artist
            commission.save()
            return redirect('client_commissions')
    else:
        form = CommissionRequestForm()

    return render(request, 'client_dashboard/request_commission.html', {
        'form': form,
        'artist': artist
    })


@login_required
def client_commissions(request):
    commissions = Commission.objects.filter(client=request.user).order_by('-created_at')
    return render(request, 'client_dashboard/client_commissions.html', {
        'commissions': commissions
    })


@login_required
def artist_commissions(request):
    commissions = Commission.objects.filter(artist=request.user).order_by('-created_at')
    return render(request, 'artist_dashboard/artist_commissions.html', {
        'commissions': commissions
    })



@login_required
def update_commission_status(request, commission_id, status):
    commission = get_object_or_404(Commission, id=commission_id, artist=request.user)
    now = timezone.now()

    if status == 'accepted':
        commission.status = 'accepted'
        commission.accepted_at = now

    elif status == 'advance_paid':
        commission.status = 'advance_paid'
        commission.advance_paid_at = now

    elif status == 'in_progress':
        commission.status = 'in_progress'
        commission.in_progress_at = now

    elif status == 'completed':
        commission.status = 'completed'
        commission.completed_at = now

    elif status == 'rejected':
        commission.status = 'rejected'
        commission.rejected_at = now
        commission.rejection_reason = request.GET.get('reason', '')

    commission.save()
    return redirect('artist_commissions')


@login_required
def upload_final_artwork(request, commission_id):
    commission = get_object_or_404(Commission, id=commission_id, artist=request.user)

    if request.method == 'POST':
        commission.final_artwork = request.FILES['final_artwork']
        commission.status = 'completed'
        commission.completed_at = timezone.now()
        commission.save()
        return redirect('artist_commissions')

    return render(request, 'artist_dashboard/upload_final_artwork.html', {'commission': commission})
