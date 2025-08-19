from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views

from event_management_system_app import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.category_list, name='category_list'),
    # Auth
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', views.register, name='register'),
    path('activate/<uidb64>/<token>/', views.activate_account, name='activate'),
    path('categories/create/', views.create_category, name='create_category'),
    path('categories/<int:category_id>/', views.category_events, name='category_events'),
    path('categories/delete/<int:category_id>/', views.delete_category, name='delete_category'),
    path('events/create/', views.create_event, name='create_event'),
    path('events/update/<int:event_id>/', views.update_event, name='update_event'),
    path('events/delete/<int:event_id>/', views.delete_event, name='delete_event'),
    path('events/<int:event_id>/', views.event_detail, name='event_detail'),
    path('events/<int:event_id>/join/', views.join_event, name='join_event'),
    path('events/<int:event_id>/toggle-wishlist/', views.toggle_wishlist, name='toggle_wishlist'),
    path('my/wishlist/', views.my_wishlist, name='my_wishlist'),
    path('event-chart/', views.event_chart, name='event_chart'),
]