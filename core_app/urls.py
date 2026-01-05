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

    



]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
