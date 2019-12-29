from django.urls import path, include, re_path
from . import views
from .views import getAjaxRequest
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required, permission_required
from django.views.generic import TemplateView

urlpatterns = [
    path('', auth_views.LoginView.as_view(template_name='bookings/login.html'), name='login'),
    path('logout', auth_views.LogoutView.as_view(template_name='bookings/login.html'), name='logout'),
    path('stats', login_required(views.stats)),
    path('create', login_required(views.create)),
    path('history', login_required(views.history)),
    path('staff_list', views.stafflist),
    path('table_layout', login_required(views.tablelayout)),
    path('changepassword', login_required(views.changepassword), name='change-password'),
    path('settings', login_required(views.settings)),
    # AJAX URLS
    path('ajax/<int:id>/', getAjaxRequest, name='ajax_newbooking'),
    path('bookings', login_required(views.bookings), name='booking-home'),
    path('download', views.download),
    path('<username>', views.book),
    
]