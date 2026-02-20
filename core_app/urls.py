from django.urls import path
from . import views
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static

from .views.auth_views import(
    register_view,
    login_view,
    logout_view,
    forgot_password,
    reset_password,
    password_reset_sent,
    password_reset_success
)

from .views.profile_views import(
    edit_profile,
    complete_profile

)

from .views.dashboard_views import(
    home,
    artist_dashboard,
    admin_dashboard,
    client_dashboard

)

from .views.admin_views import(
    admin_artists,
    admin_clients,
    admin_notifications,
    approve_artist,
    reject_artist

)

from .views.artist_views import(
    update_commission_status,
    artist_commissions,
    artist_notifications,
    artist_profile,
    artist_transactions,
    add_artworks,
    delete_artwork,
    set_total_price,

)

from .views.client_views import(
    client_commissions,
    client_notifications,
    client_transactions,
    request_commission,
    cancel_commission,
    all_artworks,
    pay_advance,
    pay_balance_choice,
    pay_balance_online,
    payment_success,
    paypal_success,
    paypal_success_balance,
    transaction_detail,

)

from .views.common_views import(
    mark_notification_read,
    delete_notification,
    unread_notification_count

)

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', home, name='home'),


    # auth
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('forgot-password/', forgot_password, name='forgot_password'),
    path('reset-password/<uidb64>/<token>/', reset_password, name='reset_password'),
    path('password-reset-success/', password_reset_success, name='password_reset_success'),
    path('password-reset-sent/', password_reset_sent, name='reset_password_sent'),


    # profile
    path('complete_profile/', complete_profile, name='complete_profile'),
    path('edit-profile/', edit_profile, name='edit_profile'),


    # dashboards
    path("admin-dashboard/", admin_dashboard, name="admin_dashboard"),
    path('artist_dashboard/', artist_dashboard, name='artist_dashboard'),
    path('client_dashboard/', client_dashboard, name='client_dashboard'),


    # admin_dashboard
    path("admin_dashboard/admin_artists/", admin_artists, name="admin_artists"),
    path("admin-clients/", admin_clients, name="admin_clients"),
    path('approve-artist/<int:user_id>/', approve_artist, name='approve_artist'),
    path('reject-artist/<int:user_id>/', reject_artist, name='reject_artist'),


    # artist_dashboard
    path('artist_dashboard/add_artworks/', add_artworks, name='add_artworks'),
    path('artwork/<int:artwork_id>/delete/', delete_artwork, name='delete_artwork'),
    path('all_artworks/', all_artworks, name='all_artworks'),
    path('artist/<int:artist_id>/', artist_profile, name='artist_profile'),
    path('artist/commissions/', artist_commissions, name='artist_commissions'),
    path('artist-notifications/', artist_notifications, name='artist_notifications'),
    path('artist/transactions/', artist_transactions, name='artist_transactions'),
    path('commission/set-total-price/<int:commission_id>/', set_total_price,name='set_total_price'),
    path('commission/<int:commission_id>/<str:status>/', update_commission_status, name='update_commission_status'),


    # client_dashboard
    path('request-commission/<int:artist_id>/', request_commission, name='request_commission'),
    path('client-commissions/', client_commissions, name='client_commissions'),
    path('commission/pay/<int:commission_id>/', pay_advance, name='pay_advance'),
    path('commission/paypal/success/<int:commission_id>/', paypal_success, name='paypal_success'),
    path("commission/paypal/balance-success/<int:commission_id>/", paypal_success_balance,name="paypal_success_balance"),
    path('client-notifications/', client_notifications, name='client_notifications'),
    path('commission/<int:commission_id>/balance-choice/', pay_balance_choice, name='pay_balance_choice'),
    path('commission/<int:commission_id>/balance-online/', pay_balance_online, name='pay_balance_online'),
    path('client/transactions/', client_transactions, name='client_transactions'),
    path('payment-success/<int:transaction_id>/', payment_success, name='payment_success'),
    path('commission/<int:commission_id>/cancel/', cancel_commission, name='cancel_commission'),
    path("transaction/<int:transaction_id>/", transaction_detail, name="transaction_detail"),


    # common
    path('notifications/mark-read/', mark_notification_read, name='mark_notification_read'),
    path('notifications/unread-count/', unread_notification_count, name='unread_notification_count'),
    path('notification/delete/<int:notification_id>/', delete_notification, name='delete_notification'),


    # path('artist/revenue/', views.artist_revenue, name='artist_revenue'),


]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
