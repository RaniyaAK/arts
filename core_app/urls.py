from django.urls import path
from . import views
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from .views import *

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', views.home, name='home'),

    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('forgot-password/', forgot_password, name='forgot_password'),
    path('reset-password/<str:email>/', reset_password, name='reset_password'),
    path('logout/', views.logout_view, name='logout'),
    
    path('artist_dashboard/', views.artist_dashboard, name='artist_dashboard'), 
    path('client_dashboard/', views.client_dashboard, name='client_dashboard'), 

    path('artist_dashboard/add_artworks', views.add_artworks, name='add_artworks'), 
    path('complete_profile/', views.complete_profile, name='complete_profile'),

    path('artwork/<int:artwork_id>/delete/', views.delete_artwork, name='delete_artwork'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),

    path('all_artworks/', views.all_artworks, name='all_artworks'), 

    path('artist/<int:artist_id>/', views.artist_profile, name='artist_profile'),


    path('request-commission/<int:artist_id>/', views.request_commission, name='request_commission'),
    path('client-commissions/', views.client_commissions, name='client_commissions'),

    path('artist/commissions/', views.artist_commissions, name='artist_commissions'),
    path('commission/<int:commission_id>/<str:status>/', views.update_commission_status, name='update_commission_status'),
    path('commission/upload/<int:commission_id>/', views.upload_final_artwork, name='upload_final_artwork'),
    path("commission/<int:commission_id>/set-advance/",views.set_advance_amount,name="set_advance_amount"),

    path('artist/commissions/', views.artist_commissions, name='artist_commissions'),
    path('artist/commission/<int:commission_id>/set_advance/', views.set_advance_amount, name='set_advance_amount'),
    path('client/commission/<int:commission_id>/pay_advance/', views.pay_advance, name='pay_advance'),
    path('artist/commission/<int:commission_id>/update/<str:status>/', views.update_commission_status, name='update_commission_status'),
]





if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



