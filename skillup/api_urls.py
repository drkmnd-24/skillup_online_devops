from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TaskViewSet, UserRegistrationViewSet, get_user_profile,
    MarkdownFileViewSet, ModifiedMarkdownFileViewSet, SubmittedMarkdownFileViewSet,
    task_detail_view, HybridLoginView, login_view
)

router = DefaultRouter()
router.register(r'tasks', TaskViewSet, basename='tasks')
router.register(r'auth/register', UserRegistrationViewSet, basename='auth-register')

router.register(r'admin/md-files', MarkdownFileViewSet, basename='md-files')
router.register(r'admin/modified-md-files', ModifiedMarkdownFileViewSet, basename='modified-md-files')
router.register(r'admin/submitted-md-files', SubmittedMarkdownFileViewSet, basename='submitted-md-files')

urlpatterns = [
    path('api/', include(router.urls)),

    path('', login_view, name='login'),
    path('users/profile/', get_user_profile, name='user-profile'),
    path('task/detail/<int:pk>/', task_detail_view, name='task_detail_api'),
    path('hybrid-login/', HybridLoginView.as_view(), name='hybrid-login'),
]
