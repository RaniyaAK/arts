
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.utils import timezone

from ..models import (
    Artwork,
    Activity,
    Commission,
    Notification,
    Transaction,
    User
)

from ..forms import ArtworkForm


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



@login_required
def artist_commissions(request):
    commissions = Commission.objects.filter(artist=request.user).order_by('-created_at')
    return render(request, 'artist_dashboard/artist_commissions.html', {
        'commissions': commissions
    })


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
def artist_transactions(request):
    if request.user.role != 'artist':
        return redirect('login')

    # Fetch only transactions where the logged-in user is the artist
    transactions = Transaction.objects.filter(
        commission__artist=request.user
    ).order_by('-created_at')

    return render(request, "artist_dashboard/artist_transactions.html", {
        "transactions": transactions
    })


def artist_profile(request, artist_id):
    artist = get_object_or_404(User, id=artist_id, role='artist')
    artworks = Artwork.objects.filter(artist=artist)

    return render(request, 'artist_dashboard/artist_profile.html', {
        'artist': artist,
        'artworks': artworks,
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

