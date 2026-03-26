from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse


from ..models import User, Notification, Commission, Transaction


@login_required
def admin_artists(request):
    if not request.user.is_superuser:
        return redirect("home")

    # Mark new artist notifications as read
    Notification.objects.filter(
        receiver=request.user,
        notification_type="new_artist",
        is_read=False
    ).update(is_read=True)

    # Fetch only artists
    artists = User.objects.filter(role="artist").order_by("-date_joined")

    context = {
        "artists": artists
    }

    return render(request, "admin_dashboard/admin_artists.html", context)


def admin_clients(request):
    clients = User.objects.filter(role="client").order_by("-date_joined")

    return render(request, "admin_dashboard/admin_clients.html", {
        "clients": clients
    })



def approve_artist(request, user_id):
    user = get_object_or_404(User, id=user_id, role='artist')
    user.is_approved = True
    user.save()
    messages.success(request, f"{user.name} has been approved as Artist.")
    return redirect('admin_dashboard')



def reject_artist(request, user_id):
    user = get_object_or_404(User, id=user_id, role='artist')
    user.delete()
    messages.error(request, f"{user.name}'s artist registration was rejected & removed.")
    return redirect('admin_dashboard')


@login_required
def admin_notifications(request):
    if not request.user.is_superuser:
        return redirect("login")

    notifications = Notification.objects.filter(
        receiver=request.user
    ).order_by('-created_at')

    # mark all as read
    Notification.objects.filter(receiver=request.user, is_read=False).update(is_read=True)

    return render(request, "notifications/admin_notifications.html", {
        "notifications": notifications
    })



@login_required
def admin_commissions(request):
    if not request.user.is_superuser:
        return redirect("login")

    commissions = Commission.objects.all().order_by("-created_at")

    return render(request, "admin_dashboard/admin_commissions.html", {
        "commissions": commissions
    })


def admin_transactions(request):

    transactions = Transaction.objects.all().order_by('-created_at')

    # Search
    search = request.GET.get('search')
    if search:
        transactions = transactions.filter(user__name__icontains=search)

    # Filter by status
    status = request.GET.get('status')
    if status:
        transactions = transactions.filter(status=status)

    # Pagination
    paginator = Paginator(transactions, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search': search,
        'status': status
    }

    return render(request, 'admin_dashboard/admin_transactions.html', context)

@login_required
def get_notifications(request):
    notifications = Notification.objects.filter(
        receiver=request.user
    ).order_by('-created_at')[:10]

    data = [
        {
            "message": n.message,
            "is_read": n.is_read
        }
        for n in notifications
    ]

    return JsonResponse({"notifications": data})