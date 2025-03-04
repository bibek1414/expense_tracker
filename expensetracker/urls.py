from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from expenses.views import google_login, google_callback
urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('', include('expenses.urls')),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('auth/google/', google_login, name='google_login'),
    path('auth/google/callback/', google_callback, name='google_callback'),
    path("__reload__/", include("django_browser_reload.urls")),
]