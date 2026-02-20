from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from ..models import Notification


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
def delete_notification(request, notification_id):
    notif = get_object_or_404(Notification, id=notification_id, receiver=request.user)
    notif.delete()
    return redirect(request.META.get("HTTP_REFERER", "client_dashboard"))







