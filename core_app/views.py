# from django.shortcuts import render, redirect, get_object_or_404
# from django.contrib.auth import authenticate, login, logout, get_user_model
# from django.contrib.auth.decorators import login_required
# from django.http import HttpResponseForbidden
# from django.views.decorators.cache import never_cache
# from django.http import JsonResponse
# from django.db.models import Q
# from django.utils import timezone
# from django.contrib import messages
# from django.conf import settings
# from django.views.decorators.csrf import csrf_exempt
# import json
# from django.views.decorators.http import require_POST

# from .forms import RegisterForm, LoginForm, ForgotPasswordForm, ResetPasswordForm
# from .forms import ArtworkForm, ProfileCompletionForm 
# from .forms import ProfileEditForm
# from .forms import CommissionRequestForm

# from .models import Artwork, Activity, Commission
# from .models import Notification
# from .models import Transaction

# import paypalrestsdk
# from django.db.models import Sum
# from django.contrib.auth.tokens import default_token_generator
# from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
# from django.utils.encoding import force_bytes
# from django.core.mail import send_mail

# paypalrestsdk.configure({
#     "mode": settings.PAYPAL_MODE,
#     "client_id": settings.PAYPAL_CLIENT_ID,
#     "client_secret": settings.PAYPAL_CLIENT_SECRET
# })


# User = get_user_model()


# # ________________________________________________________________________________________________________________________



# @login_required
# def unread_notification_count(request):
#     count = Notification.objects.filter(
#         receiver=request.user,
#         is_read=False
#     ).count()
#     return JsonResponse({'count': count})



# @login_required
# @require_POST
# def mark_notification_read(request):
#     Notification.objects.filter(
#         receiver=request.user,
#         is_read=False
#     ).update(is_read=True)

#     return JsonResponse({'status': 'ok'})



# @login_required
# def delete_notification(request, notification_id):
#     notif = get_object_or_404(Notification, id=notification_id, receiver=request.user)
#     notif.delete()
#     return redirect(request.META.get("HTTP_REFERER", "client_dashboard"))







