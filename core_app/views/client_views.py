from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.http import HttpResponseForbidden
from django.conf import settings

from ..models import Commission, Notification, Transaction, Artwork, User

from ..forms import CommissionRequestForm

import paypalrestsdk

paypalrestsdk.configure({
    "mode": settings.PAYPAL_MODE,
    "client_id": settings.PAYPAL_CLIENT_ID,
    "client_secret": settings.PAYPAL_CLIENT_SECRET
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

            # NEW FIELDS: Save location
            commission.delivery_address = form.cleaned_data.get('delivery_address')
            commission.delivery_latitude = form.cleaned_data.get('delivery_latitude')
            commission.delivery_longitude = form.cleaned_data.get('delivery_longitude')

            commission.phone_number = form.cleaned_data.get('phone_number')


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
def client_notifications(request):
    notifications = Notification.objects.filter(
        receiver=request.user
    ).order_by('-created_at')

    return render(request, 'notifications/client_notifications.html', {
        'notifications': notifications
    })



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



@login_required
def client_transactions(request):
    # Only show transactions of logged-in user
    transactions = Transaction.objects.filter(user=request.user).order_by('-created_at')

    context = {
        "transactions": transactions
    }
    return render(request, "client_dashboard/client_transactions.html", context)



@login_required
def all_artworks(request):
    if request.user.role != 'client':
        return redirect('login')

    artworks = Artwork.objects.all().order_by('-created_at')
    return render(request, 'client_dashboard/all_artworks.html', {'artworks': artworks})


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

