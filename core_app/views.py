from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth import authenticate, login,logout,get_user_model
from django.contrib import messages
from .forms import RegisterForm, LoginForm, ForgotPasswordForm, ResetPasswordForm
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from django.contrib.auth.decorators import login_required
from .forms import ArtworkForm
from .models import Artwork,Activity
from django.http import HttpResponseForbidden


User = get_user_model()

def home(request):
    return render(request,'home.html')


def logout_view(request):
    logout(request)
    messages.success(request, "Logged out successfully")
    return redirect('login')

@login_required
def artist_dashboard(request):
    if request.user.role != 'artist':
        return redirect('login')

    artworks = Artwork.objects.filter(artist=request.user).order_by('-created_at')
    activities = Activity.objects.filter(user=request.user).order_by('-created_at')[:10]

    return render(request, 'dashboards/artist_dashboard.html', {
        'artworks': artworks,
        'activities': activities,   # ✅ THIS WAS MISSING
        'numbers': range(1, 4),
    })




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


    #    ______________________________________________________________________________________________________________


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
                artwork_title=artwork.title,
                action='added'
            )

            return redirect('artist_dashboard')
    else:
        form = ArtworkForm()

    return render(request, 'artist_dashboard/add_artworks.html', {'form': form})


@login_required
def edit_artwork(request, artwork_id):
    artwork = get_object_or_404(Artwork, id=artwork_id)

    if request.user != artwork.artist:
        return HttpResponseForbidden()

    if request.method == 'POST':
        form = ArtworkForm(request.POST, request.FILES, instance=artwork)
        if form.is_valid():
            form.save()

            Activity.objects.create(
                user=request.user,
                artwork_title=artwork.title,
                action='edited'
            )

            # ✅ Redirect to dashboard so changes appear immediately
            return redirect('artist_dashboard')
    else:
        form = ArtworkForm(instance=artwork)

    return render(request, 'artist_dashboard/edit_artwork.html', {'form': form})


from django.views.decorators.cache import never_cache

@never_cache
@login_required
def delete_artwork(request, artwork_id):
    artwork = get_object_or_404(
        Artwork,
        id=artwork_id,
        artist=request.user
    )

    if request.method == 'POST':
        Activity.objects.create(
            user=request.user,
            artwork_title=artwork.title,
            action='deleted'
        )

        artwork.delete()
        messages.success(request, "Artwork deleted successfully.")
        return redirect('artist_dashboard')  

    return render(request, 'artist_dashboard/delete_artwork.html', {
        'artwork': artwork
    })


   # _________________________________________________________________________________________________________________


def artwork_detail_for_artist(request, artwork_id):
    artwork = Artwork.objects.get(id=artwork_id)

    if request.user.is_authenticated and request.user == artwork.artist:
        return render(
            request,
            'artist_dashboard/artwork_detail_artist.html',
            {'artwork': artwork}
        )

    return render(
        request,
        'client_dashboard/artwork_detail_client.html',
        {'artwork': artwork}
    )


@login_required
def client_dashboard(request):
    if request.user.role != 'client':
        return redirect('login')

    artworks = Artwork.objects.all().order_by('-created_at')[:6]
    featured_artists = User.objects.filter(role='artist') 

    return render(request, 'dashboards/client_dashboard.html', {
        'artworks': artworks,
        'featured_artists': featured_artists,
    })

@login_required
def artist_artworks_for_client(request, artist_id):
    artist = get_object_or_404(User, id=artist_id, role='artist')
    artworks = Artwork.objects.filter(artist=artist).order_by('-created_at')

    return render(request, 'artist_dashboard/artworks.html', {
        'artist': artist,
        'artworks': artworks
    })

@login_required
def artist_my_artworks(request):
    if request.user.role != 'artist':
        return HttpResponseForbidden("Only artists can view this page")

    artworks = Artwork.objects.filter(artist=request.user).order_by('-created_at')

    return render(request, 'artist_dashboard/artworks.html', {
        'artworks': artworks
    })

@login_required
def all_artworks(request):
    if request.user.role != 'client':
        return redirect('login')

    artworks = Artwork.objects.all().order_by('-created_at') 

    return render(request, 'client_dashboard/all_artworks.html', {
        'artworks': artworks
    })

