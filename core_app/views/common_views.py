from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from ..models import Notification

from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from groq import Groq
import json

client = Groq(api_key=settings.GROQ_API_KEY)


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



@csrf_exempt
def chatbot_api(request):

    if request.method == "POST":

        data = json.loads(request.body)
        message = data.get("message", "")

        try:
            chat = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "You are an AI assistant for Paletra art platform."},
                    {"role": "user", "content": message}
                ]
            )

            reply = chat.choices[0].message.content

        except Exception as e:
            print("AI ERROR:", e)   
            reply = "Sorry, the AI is temporarily unavailable."

        return JsonResponse({"reply": reply})