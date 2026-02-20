from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from ..models import User, Notification


def admin_artists(request):
    if not request.user.is_superuser:
        return redirect("home")

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