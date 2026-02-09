from django.urls import path
from . import views
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', views.home, name='home'),

    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    path('artist_dashboard/', views.artist_dashboard, name='artist_dashboard'),
    path('client_dashboard/', views.client_dashboard, name='client_dashboard'),

    path('complete_profile/', views.complete_profile, name='complete_profile'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),

    path('artist_dashboard/add_artworks/', views.add_artworks, name='add_artworks'),
    path('artwork/<int:artwork_id>/delete/', views.delete_artwork, name='delete_artwork'),
    path('all_artworks/', views.all_artworks, name='all_artworks'),

    path('artist/<int:artist_id>/', views.artist_profile, name='artist_profile'),

    path('request-commission/<int:artist_id>/', views.request_commission, name='request_commission'),
    path('client-commissions/', views.client_commissions, name='client_commissions'),
    path('artist/commissions/', views.artist_commissions, name='artist_commissions'),


    path('commission/pay/<int:commission_id>/', views.pay_advance, name='pay_advance'),
    path('commission/paypal/success/<int:commission_id>/', views.paypal_success, name='paypal_success'),
    path("commission/paypal/balance-success/<int:commission_id>/",views.paypal_success_balance,name="paypal_success_balance"),


    path('notifications/mark-read/', views.mark_notification_read, name='mark_notification_read'),


    path('artist-notifications/', views.artist_notifications, name='artist_notifications'),

    path('client-notifications/', views.client_notifications, name='client_notifications'),

    path('notifications/unread-count/', views.unread_notification_count, name='unread_notification_count'),

    path('commission/set-total-price/<int:commission_id>/',views.set_total_price,name='set_total_price'),


    path('commission/<int:commission_id>/balance-choice/', views.pay_balance_choice, name='pay_balance_choice'),
    path('commission/<int:commission_id>/balance-online/', views.pay_balance_online, name='pay_balance_online'),

    path('commission/<int:commission_id>/cancel/', views.cancel_commission, name='cancel_commission'),


    path('commission/<int:commission_id>/<str:status>/', views.update_commission_status, name='update_commission_status'),

    path('commission/<int:commission_id>/cancel/',views.cancel_commission,name='cancel_commission'),

    path('client/transactions/', views.client_transactions, name='client_transactions'),

    # path('artist/revenue/', views.artist_revenue, name='artist_revenue'),
    path('artist/transactions/', views.artist_transactions, name='artist_transactions'),
    path("transaction/<int:transaction_id>/", views.transaction_detail, name="transaction_detail"),
    path('payment-success/<int:transaction_id>/', views.payment_success, name='payment_success'),
    path('notification/delete/<int:notification_id>/', views.delete_notification, name='delete_notification'),
    path("admin-dashboard/", views.admin_dashboard, name="admin_dashboard"),

    path("admin_dashboard/admin_artists/", views.admin_artists, name="admin_artists"),



    path("admin-clients/", views.admin_clients, name="admin_clients"),





]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
