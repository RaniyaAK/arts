from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.views.decorators.cache import never_cache
from django.http import JsonResponse
from django.db.models import Q
from django.utils import timezone
from django.contrib import messages
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

from .forms import RegisterForm, LoginForm, ForgotPasswordForm, ResetPasswordForm
from .forms import ArtworkForm, ProfileCompletionForm 
from .forms import ProfileEditForm
from .forms import CommissionRequestForm
from .forms import SetAdvanceAmountForm

from .models import Artwork, Activity
from .models import Commission

import razorpay

import paypalrestsdk
from django.shortcuts import redirect
from django.conf import settings

paypalrestsdk.configure({
    "mode": settings.PAYPAL_MODE,
    "client_id": settings.PAYPAL_CLIENT_ID,
    "client_secret": settings.PAYPAL_CLIENT_SECRET
})


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
            if user.role == 'artist':
                return redirect('artist_dashboard')
            elif user.role == 'client':
                return redirect('client_dashboard')
        else:
            messages.error(request, "Invalid username or password.")

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


# ------------------------ Reset Password Fix ------------------------
def reset_password(request, email):
    user = User.objects.filter(email=email).first()
    if not user:
        messages.error(request, "Invalid email.")
        return redirect('forgot_password')

    if request.method == 'POST':
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, 'reset_password.html')

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

from django.db.models import Sum

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from .models import Artwork, Activity, Commission
from django.db.models import Sum

@login_required
def artist_dashboard(request):
    if request.user.role != 'artist':
        return redirect('login')

    artworks = Artwork.objects.filter(artist=request.user).order_by('-created_at')
    activities = Activity.objects.filter(user=request.user).order_by('-created_at')[:10]
    commissions = Commission.objects.filter(artist=request.user).order_by('-created_at')

    # Revenue calculations
    advance_revenue = commissions.filter(advance_paid=True).aggregate(total=Sum('advance_amount'))['total'] or 0
    # Full revenue: consider completed commissions; for now sum advance + remaining
    full_revenue = commissions.filter(status='completed').aggregate(total=Sum('advance_amount'))['total'] or 0
    # total revenue = advance + full? or full already includes advance? Adjust as needed.

    return render(request, 'dashboards/artist_dashboard.html', {
        'artworks': artworks,
        'activities': activities,
        'numbers': range(1, 4),
        'commissions': commissions,
        'advance_revenue': advance_revenue,
        'full_revenue': full_revenue,
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

# ------------------------ Add Artwork ------------------------
@login_required
def add_artworks(request):
    if request.method == 'POST':
        form = ArtworkForm(request.POST, request.FILES)
        if form.is_valid():
            artwork = form.save(commit=False)
            artwork.artist = request.user
            artwork.save()

            # Log activity with actual artwork title
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
            # Set default advance amount if empty
            if not commission.advance_amount:
                commission.advance_amount = 0  # or some default like 500
            commission.save()
            messages.success(request, "Commission requested successfully!")
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



# ------------------------ Update Commission Status ------------------------
@login_required
def update_commission_status(request, commission_id, status):
    commission = get_object_or_404(Commission, id=commission_id, artist=request.user)
    now = timezone.now()

    # Enforce workflow order:
    # pending → accepted → advance_paid → in_progress → completed
    # rejected can happen from pending or accepted only
    if status == 'accepted':
        if commission.status != 'pending':
            messages.error(request, "Cannot accept this commission at this stage.")
            return redirect('artist_commissions')
        commission.status = 'accepted'
        commission.accepted_at = now

    elif status == 'advance_paid':
        if commission.status != 'accepted':
            messages.error(request, "Cannot mark advance as paid before accepting the commission.")
            return redirect('artist_commissions')
        commission.status = 'advance_paid'
        commission.advance_paid_at = now

    elif status == 'in_progress':
        if commission.status != 'advance_paid':
            messages.error(request, "Cannot start work before advance is paid.")
            return redirect('artist_commissions')
        commission.status = 'in_progress'
        commission.in_progress_at = now

    elif status == 'completed':
        if commission.status != 'in_progress':
            messages.error(request, "Cannot complete work before starting it.")
            return redirect('artist_commissions')
        commission.status = 'completed'
        commission.completed_at = now

    elif status == 'rejected':
        if commission.status not in ['pending', 'accepted']:
            messages.error(request, "Cannot reject a commission at this stage.")
            return redirect('artist_commissions')
        commission.status = 'rejected'
        commission.rejected_at = now
        # Get reason from POST to match form submission
        commission.rejection_reason = request.POST.get('reason', '')

    commission.save()
    messages.success(request, f"Commission status updated to {commission.status}.")
    return redirect('artist_commissions')

@login_required
def pay_advance(request, commission_id):
    commission = get_object_or_404(Commission, id=commission_id, client=request.user)
    
    if not commission.advance_amount or commission.advance_paid:
        messages.info(request, "Advance already paid or not set.")
        return redirect("client_commissions")

    payment = paypalrestsdk.Payment({
        "intent": "sale",
        "payer": {"payment_method": "paypal"},
        "redirect_urls": {
            "return_url": request.build_absolute_uri(f"/commission/paypal/success/{commission.id}/"),
            "cancel_url": request.build_absolute_uri("/client-commissions/")
        },
        "transactions": [{
            "item_list": {
                "items": [{
                    "name": commission.title,
                    "sku": f"commission_{commission.id}",
                    "price": str(commission.advance_amount),
                    "currency": "USD",

                    "quantity": 1
                }]
            },
            "amount": {
            "total": str(commission.advance_amount),
            "currency": "USD"

            },
            "description": f"Advance payment for commission {commission.title}"
        }]
    })

    if payment.create():
        for link in payment.links:
            if link.rel == "approval_url":
                return redirect(link.href)
    else:
        messages.error(request, "Error creating PayPal payment.")
        return redirect("client_commissions")

@login_required
def paypal_success(request, commission_id):
    commission = get_object_or_404(Commission, id=commission_id, client=request.user)
    payment_id = request.GET.get('paymentId')
    payer_id = request.GET.get('PayerID')

    payment = paypalrestsdk.Payment.find(payment_id)

    if payment.execute({"payer_id": payer_id}):
        commission.advance_paid = True
        commission.status = "advance_paid"
        commission.advance_paid_at = timezone.now()
        commission.save()
        messages.success(request, "Advance payment successful via PayPal!")
    else:
        messages.error(request, "Payment failed. Please try again.")

    return redirect("client_commissions")



from django.views.decorators.http import require_POST


@login_required
@require_POST
def set_advance_amount(request, commission_id):
    commission = get_object_or_404(
        Commission,
        id=commission_id,
        artist=request.user
    )

    advance_amount = request.POST.get("advance_amount")

    if advance_amount:
        commission.advance_amount = advance_amount
        commission.save()

        messages.success(request, "Advance amount requested successfully.")
    else:
        messages.error(request, "Please enter a valid advance amount.")

    return redirect("artist_commissions")


