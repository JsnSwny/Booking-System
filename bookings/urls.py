from django.urls import path, include, re_path
from . import views
from .views import getAjaxRequest
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required, permission_required
from django.views.generic import TemplateView

urlpatterns = [
    path('login', auth_views.LoginView.as_view(template_name='bookings/login.html'), name='login'),
    path('logout', auth_views.LogoutView.as_view(template_name='bookings/logout.html'), name='logout'),
    path('', views.home, name='booking-home'),
    path('stats', login_required(TemplateView.as_view(template_name='bookings/stats.html'))),
    path('create', login_required(views.create)),
    path('history', login_required(views.history)),
    path('staff_list', views.stafflist),
    path('table_layout', views.tablelayout),
    # AJAX URLS
    path('ajax/<int:id>/', getAjaxRequest, name='ajax_newbooking'),
    path('bookings', login_required(views.bookings)),
]