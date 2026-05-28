from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),

    path('<int:pk>/', views.UserDetailView.as_view(), name='user_detail'),
    path('<int:pk>/edit/', views.UserEditView.as_view(), name='user_edit'),
    path('<int:pk>/change-password/', views.PasswordChangeView.as_view(), name='change_password'),
    
    path('list/', views.UserListView.as_view(), name='user_list'),
]