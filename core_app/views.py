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
import json
from django.views.decorators.http import require_POST

from .forms import RegisterForm, LoginForm, ForgotPasswordForm, ResetPasswordForm
from .forms import ArtworkForm, ProfileCompletionForm 
from .forms import ProfileEditForm
from .forms import CommissionRequestForm

from .models import Artwork, Activity, Commission
from .models import Notification
from .models import Transaction

import paypalrestsdk
from django.db.models import Sum
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail



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
        user.is_profile_complete = False  
        user.save()

        login(request, user)  
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


#  ________________________________________________________________________________________________________________________


@login_required
def artist_dashboard(request):
    if request.user.role != 'artist':
        return redirect('login')

    artworks = Artwork.objects.filter(
        artist=request.user
    ).order_by('-created_at')

    activities = Activity.objects.filter(
        user=request.user
    ).order_by('-created_at')[:10]

    commissions = Commission.objects.filter(
        artist=request.user
    )

    advance_revenue = commissions.filter(
        advance_paid=True
    ).aggregate(
        total=Sum('advance_amount')
    )['total'] or 0

    balance_revenue = commissions.filter(
        balance_paid=True
    ).aggregate(
        total=Sum('total_price') - Sum('advance_amount')
    )

    balance_revenue = sum(
        (c.total_price - c.advance_amount)
        for c in commissions.filter(balance_paid=True)
        if c.total_price and c.advance_amount
    )

    full_revenue = advance_revenue + balance_revenue

    return render(request, 'dashboards/artist_dashboard.html', {
        'artworks': artworks,
        'activities': activities,
        'commissions': commissions,
        'advance_revenue': advance_revenue,
        'balance_revenue': balance_revenue,
        'full_revenue': full_revenue,
    })
@login_required
def client_dashboard(request):
    if request.user.role != 'client':
        return redirect('login')

    if not request.user.is_profile_complete:
        return redirect('complete_profile')

    search_query = request.GET.get('search', '')

    if search_query:
        featured_artists = User.objects.filter(
            role='artist',
            name__icontains=search_query
        )
    else:
        featured_artists = User.objects.filter(role='artist')

    all_artworks = Artwork.objects.all().order_by('-created_at')
    artworks = all_artworks[:6]
    artwork_count = all_artworks.count()

    transactions = Transaction.objects.filter(
        user=request.user
    ).order_by('-created_at')

    return render(
        request,
        'dashboards/client_dashboard.html',
        {
            'artworks': artworks,
            'featured_artists': featured_artists,
            'artwork_count': artwork_count,
            'transactions': transactions,  
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

            Activity.objects.create(
                user=request.user,
                artwork_title=artwork.artwork_title,
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
            if not commission.advance_amount:
                commission.advance_amount = 0
            commission.save()


            client_name = request.user.name or "A client"

            Notification.objects.create(
                receiver=artist,
                commission=commission,
                message=f"{client_name} requested a commission: {commission.title}",
                notification_type='commission_request'
            )

            messages.success(request, "Commission requested successfully!")
            return redirect('client_commissions')
        else:
            # Debug: print errors if form fails
            print("Form errors:", form.errors)
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
    commission = get_object_or_404(
        Commission,
        id=commission_id,
        artist=request.user
    )
    now = timezone.now()

    # ---------------- WORKFLOW RULES ----------------
    if status == 'accepted':
        if commission.status != 'pending':
            messages.error(request, "Cannot accept at this stage.")
            return redirect('artist_commissions')
        commission.status = 'accepted'
        commission.accepted_at = now

        Notification.objects.create(
            receiver=commission.client,
            commission=commission,
            message=f"Your commission '{commission.title}' ({commission.commission_id}) has been accepted by {request.user.name or request.user.username}",
                                                                                                             
            notification_type='accepted'
        )


    elif status == 'rejected':
        if commission.status not in ['pending', 'accepted']:
            messages.error(request, "Cannot reject at this stage.")
            return redirect('artist_commissions')
        commission.status = 'rejected'
        commission.rejected_at = now
        commission.rejection_reason = request.POST.get('reason', '')

        Notification.objects.create(
            receiver=commission.client,
            commission=commission,
            message=f"Your commission '{commission.title}' ({commission.commission_id}) has been rejected by {request.user.get_full_name() or request.user.username}",
            notification_type='rejected'
        )


    elif status == 'in_progress':
        if commission.status != 'advance_paid':
            messages.error(request, "Advance must be paid before starting work.")
            return redirect('artist_commissions')
        commission.status = 'in_progress'
        commission.in_progress_at = now

    elif status == 'completed':
        if commission.status != 'in_progress':
            messages.error(request, "Work must be in progress first.")
            return redirect('artist_commissions')
        commission.status = 'completed'
        commission.completed_at = now

    elif status == 'shipping':
        if commission.status != 'completed':
            messages.error(request, "Work must be completed before shipping.")
            return redirect('artist_commissions')

        commission.status = 'shipping'
        commission.shipping_at = now

        if commission.payment_mode == 'offline' and not commission.balance_paid:
            commission.balance_paid = True
            commission.balance_paid_at = now

            Transaction.objects.create(
                user=commission.client,
                commission=commission,
                amount=commission.total_price - commission.advance_amount,
                transaction_type='balance',
                payment_mode='offline',
                status='completed',
                description=f"Offline balance payment collected for {commission.title}"
            )

            # Notify client
            Notification.objects.create(
                receiver=commission.client,
                commission=commission,
                message=f"Offline payment collected for commission '{commission.title}' ({commission.commission_id})",
                notification_type='balance_paid'
            )

        Notification.objects.create(
            receiver=commission.client,
            commission=commission,
            message=f"Your commission '{commission.title}' ({commission.commission_id}) has been shipped",
            notification_type='shipped'
        )


    elif status == 'delivered':
        if commission.status != 'shipping':
            messages.error(request, "Artwork must be shipped before delivery.")
            return redirect('artist_commissions')

        remaining = commission.total_price - commission.advance_amount
        if remaining > 0 and not commission.balance_paid:
            messages.error(request, "Cannot mark as delivered. Client has not paid the remaining balance yet.")
            return redirect('artist_commissions')

        commission.status = 'delivered'
        commission.delivered_at = now

        # Notify client
        Notification.objects.create(
            receiver=commission.client,
            commission=commission,
            message=f"Your commission '{commission.title}' ({commission.commission_id}) has been delivered",
            notification_type='delivered'
        )



    else:
        messages.error(request, "Invalid status.")
        return redirect('artist_commissions')

    commission.save()
    messages.success(request, f"Commission marked as {commission.status}.")
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

        # CREATE TRANSACTION
        transaction = Transaction.objects.create(
            user=request.user,
            commission=commission,
            amount=commission.advance_amount,
            transaction_type='advance',
            payment_mode='online',
            status='completed',
            description=f"Advance payment for {commission.title}"
        )

        Notification.objects.create(
            receiver=commission.artist,
            message=f"Advance payment received for commission: {commission.title} ({commission.commission_id})",
            notification_type='advance_paid'
        )

        messages.success(request, "Advance payment successful via PayPal!")

        # 🔹 Redirect to Payment Success page
        return redirect('payment_success', transaction_id=transaction.id)

    else:
        messages.error(request, "Payment failed. Please try again.")
        return redirect("client_commissions")




@login_required
@require_POST
def set_total_price(request, commission_id):
    commission = get_object_or_404(
        Commission,
        id=commission_id,
        artist=request.user
    )

    total_price = request.POST.get("total_price")

    if total_price:
        total_price = float(total_price)

        commission.total_price = total_price
        commission.advance_amount = round(total_price * 0.30, 2) 
        commission.save()

        messages.success(
            request,
            f"Total price set. Advance automatically calculated as ₹{commission.advance_amount}"
        )
    else:
        messages.error(request, "Please enter a valid total price.")

    return redirect("artist_commissions")


@login_required
def artist_notifications(request):
    notifications = Notification.objects.filter(
        receiver=request.user
    ).order_by('-created_at')

    return render(request, 'notifications/artist_notifications.html', {
        'notifications': notifications
    })


@login_required
def client_notifications(request):
    notifications = Notification.objects.filter(
        receiver=request.user
    ).order_by('-created_at')

    return render(request, 'notifications/client_notifications.html', {
        'notifications': notifications
    })


@login_required
def unread_notification_count(request):
    count = Notification.objects.filter(
        receiver=request.user,
        is_read=False
    ).count()
    return JsonResponse({'count': count})


@login_required
@require_POST
def mark_notification_read(request):
    Notification.objects.filter(
        receiver=request.user,
        is_read=False
    ).update(is_read=True)

    return JsonResponse({'status': 'ok'})


@login_required
@require_POST
def pay_balance_choice(request, commission_id):
    commission = get_object_or_404(
        Commission,
        id=commission_id,
        client=request.user
    )

    method = request.POST.get('method')

    if commission.balance_paid:
        messages.info(request, "Balance already paid.")
        return redirect('client_commissions')

    if commission.status != 'completed':
        messages.error(request, "Balance payment not allowed at this stage.")
        return redirect('client_commissions')

    remaining = commission.total_price - commission.advance_amount
    if remaining <= 0:
        messages.info(request, "No balance amount remaining.")
        return redirect('client_commissions')

    # ✅ Save payment method
    commission.payment_mode = method
    commission.save()

    if method == 'online':
        return redirect('pay_balance_online', commission_id=commission.id)

    elif method == 'offline':
        commission.payment_mode = 'offline'
        commission.save()

        messages.success(
            request,
            "Offline payment selected. You will pay the artist after shipping."
        )
        return redirect('client_commissions')



@login_required
def pay_balance_online(request, commission_id):
    commission = get_object_or_404(
        Commission,
        id=commission_id,
        client=request.user
    )

    remaining = commission.total_price - commission.advance_amount

    if commission.status != 'completed':
        messages.error(request, "Balance payment not allowed at this stage.")
        return redirect('client_commissions')


    if commission.balance_paid:
        messages.info(request, "Balance already paid.")
        return redirect('client_commissions')


    if remaining <= 0:
        messages.info(request, "No balance remaining.")
        return redirect('client_commissions')

    payment = paypalrestsdk.Payment({
        "intent": "sale",
        "payer": {"payment_method": "paypal"},
        "redirect_urls": {
            "return_url": request.build_absolute_uri(
                f"/commission/paypal/balance-success/{commission.id}/"
            ),



            "cancel_url": request.build_absolute_uri("/client-commissions/")
        },
        "transactions": [{
            "amount": {
                "total": str(remaining),
                "currency": "USD"
            },
            "description": f"Balance payment for commission {commission.title}"
        }]
    })

    if payment.create():
        for link in payment.links:
            if link.rel == "approval_url":
                return redirect(link.href)

    messages.error(request, "Unable to initiate balance payment.")
    return redirect('client_commissions')


@login_required
def paypal_success_balance(request, commission_id):
    commission = get_object_or_404(Commission, id=commission_id, client=request.user)

    payment_id = request.GET.get('paymentId')
    payer_id = request.GET.get('PayerID')

    payment = paypalrestsdk.Payment.find(payment_id)

    if payment.execute({"payer_id": payer_id}):
        commission.balance_paid = True
        commission.balance_paid_at = timezone.now()
        commission.save()

        # CREATE BALANCE TRANSACTION
        transaction = Transaction.objects.create(
            user=request.user,
            commission=commission,
            amount=commission.total_price - commission.advance_amount,
            transaction_type='balance',
            payment_mode='online',
            status='completed',
            description=f"Balance payment for {commission.title}"
        )

        messages.success(request, "Balance payment successful!")

        Notification.objects.create(
            receiver=commission.artist,
            commission=commission,
            message=f"Balance payment received for '{commission.title}'",
            notification_type='balance_paid'
        )

        # 🔹 Redirect to Payment Success page
        return redirect('payment_success', transaction_id=transaction.id)

    else:
        messages.error(request, "Balance payment failed.")
        return redirect("client_commissions")


@login_required
@require_POST
def cancel_commission(request, commission_id):
    commission = get_object_or_404(Commission, id=commission_id)

    # Only client OR artist can cancel
    if request.user not in [commission.client, commission.artist]:
        return HttpResponseForbidden()

    # ❌ Cannot cancel after shipping
    if commission.status in ['shipping', 'delivered']:
        messages.error(request, "Cannot cancel after shipping.")
        return redirect(
            'client_commissions' if request.user == commission.client else 'artist_commissions'
        )

    commission.status = 'cancelled'
    commission.cancelled_at = timezone.now()
    commission.cancelled_by = 'client' if request.user == commission.client else 'artist'
    commission.cancellation_reason = request.POST.get('reason', '')
    commission.save()

    # 🔔 Notify other party
    receiver = commission.artist if request.user == commission.client else commission.client

    Notification.objects.create(
        receiver=receiver,
        commission=commission,
        message=f"Commission '{commission.title}' ({commission.commission_id}) has been cancelled.",
        notification_type='cancelled'
    )

    messages.success(request, "Commission cancelled successfully.")
    return redirect(
        'client_commissions' if request.user == commission.client else 'artist_commissions'
    )



User = get_user_model()

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

    return render(request, 'forgot_password.html')




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

        user.set_password(password)
        user.save()

        messages.success(request, "Password reset successful. Please login.")
        return redirect('login')

    return render(request, 'auth/reset_password.html')



@login_required
def client_transactions(request):
    # Only show transactions of logged-in user
    transactions = Transaction.objects.filter(user=request.user).order_by('-created_at')

    context = {
        "transactions": transactions
    }
    return render(request, "client_dashboard/client_transactions.html", context)


def artist_transactions(request):
    # Example dummy data
    transactions = []  
    return render(request, "artist_dashboard/artist_transactions.html", {"transactions": transactions})

@login_required
def transaction_detail(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id, user=request.user)
    commission = transaction.commission  # linked commission

    return render(request, "client_dashboard/transaction_detail.html", {
        "transaction": transaction,
        "commission": commission,
    })


@login_required
def payment_success(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id, user=request.user)
    commission = transaction.commission

    return render(request, "client_dashboard/payment_success.html", {
        "transaction": transaction,
        "commission": commission,
    })
