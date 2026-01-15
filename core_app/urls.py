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
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/<str:email>/', views.reset_password, name='reset_password'),
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


    path('notifications/mark-read/', views.mark_notification_read, name='mark_notification_read'),


    path('artist-notifications/', views.artist_notifications, name='artist_notifications'),

    path('client-notifications/', views.client_notifications, name='client_notifications'),

    path('notifications/unread-count/', views.unread_notification_count, name='unread_notification_count'),

    path('commission/set-total-price/<int:commission_id>/',views.set_total_price,name='set_total_price'),


    path('commission/<int:commission_id>/balance-choice/', views.pay_balance_choice, name='pay_balance_choice'),
    path('commission/<int:commission_id>/balance-online/', views.pay_balance_online, name='pay_balance_online'),

    path('commission/<int:commission_id>/<str:status>/', views.update_commission_status, name='update_commission_status'),

    # path('artist/revenue/', views.artist_revenue, name='artist_revenue'),


]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
