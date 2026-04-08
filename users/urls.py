# users/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # 用户相关
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    path('upload-student-card/', views.UploadStudentCardView.as_view(), name='upload_student_card'),
    path('apply-creator/', views.ApplyCreatorView.as_view(), name='apply-creator'),
    path('can-apply-creator/', views.CanApplyCreatorView.as_view(), name='can-apply-creator'),
    
    # 管理员审核相关
    path('admin/pending-creators/', views.PendingCreatorApplicationsView.as_view(), name='admin-pending-creators'),
    path('admin/review-creator/<int:user_id>/', views.ReviewCreatorApplicationView.as_view(), name='admin-review-creator'),
]