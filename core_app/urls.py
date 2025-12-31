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
    path('artist_dashboard/artist_my_artworks/', views.artist_my_artworks, name='artist_my_artworks'),
    path('artwork/<int:artwork_id>/edit/', views.edit_artwork, name='edit_artwork'),
    path('artwork/<int:artwork_id>/delete/', views.delete_artwork, name='delete_artwork'),

    path('artwork/<int:artwork_id>/', views.artwork_detail_for_artist, name='artwork_detail_for_artist'),

    path('client_dashbaord/<int:artist_id>/artist_artworks_for_client/',views.artist_artworks_for_client,name='artist_artworks_for_client'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
