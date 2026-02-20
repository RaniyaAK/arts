from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib import messages

from ..models import Artwork, Activity, Commission, Transaction,Notification

User = get_user_model()


def home(request):
    return render(request, 'dashboards/home.html')


@login_required
def artist_dashboard(request):

    if request.user.role != 'artist':
        return redirect('login')

    if not request.user.is_profile_complete:
        return redirect('complete_profile')


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



def admin_dashboard(request):
    if not request.user.is_superuser:
        return redirect("login")

    # ------------------ METRICS ------------------
    total_users = User.objects.count()
    total_artists = User.objects.filter(role="artist").count()
    total_clients = User.objects.filter(role="client").count()

    total_commissions = Commission.objects.count()
    pending_commissions = Commission.objects.filter(status="pending").count()
    completed_commissions = Commission.objects.filter(status="delivered").count()

    total_transactions = Transaction.objects.count()
    revenue = Transaction.objects.filter(status="completed").aggregate(Sum("amount"))["amount__sum"] or 0

    # ------------------ RECENT LISTS ------------------
    recent_users = User.objects.order_by("-date_joined")[:5]
    recent_commissions = Commission.objects.order_by("-created_at")[:5]
    recent_transactions = Transaction.objects.order_by("-created_at")[:5]

    recent_artists = User.objects.filter(role="artist").order_by("-date_joined")[:5]
    recent_clients = User.objects.filter(role="client").order_by("-date_joined")[:5]

    # ------------------ PENDING ARTIST APPROVALS ------------------
    pending_artists = User.objects.filter(role="artist", is_approved=False).order_by("-date_joined")

    # ------------------ NEW ARTIST NOTIFICATIONS ------------------
    new_artist_notifications = Notification.objects.filter(
        receiver=request.user,
        notification_type='new_artist'
    ).order_by('-created_at')

    new_artist_count = new_artist_notifications.filter(is_read=False).count()

    # ------------------ RENDER ------------------
    return render(request, "dashboards/admin_dashboard.html", {
        # Metrics
        "total_users": total_users,
        "total_artists": total_artists,
        "total_clients": total_clients,
        "total_commissions": total_commissions,
        "pending_commissions": pending_commissions,
        "completed_commissions": completed_commissions,
        "total_transactions": total_transactions,
        "revenue": revenue,

        # Recent lists
        "recent_users": recent_users,
        "recent_commissions": recent_commissions,
        "recent_transactions": recent_transactions,
        "recent_artists": recent_artists,
        "recent_clients": recent_clients,

        # Pending artist approvals
        "pending_artists": pending_artists,

        # New artist notifications
        "new_artist_notifications": new_artist_notifications,
        "new_artist_count": new_artist_count,
    })

