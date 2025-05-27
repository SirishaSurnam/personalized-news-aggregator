from django.urls import path
from . import views # Import views from the current app

urlpatterns = [
    path('login/', views.CustomLoginView.as_view(), name='login'), [cite: 98]
    path('logout/', views.CustomLogoutView.as_view(), name='logout'), [cite: 98]
    path('register/', views.register, name='register'), [cite: 98]
]