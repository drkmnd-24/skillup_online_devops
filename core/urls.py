from django.contrib import admin
from django.urls import path, include
from skillup.views import login_view, register_view, index_view, task_detail_view

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("main_app.api_urls")),
    path("login/", login_view, name="login"),
    path("register/", register_view, name="register-user"),
    path("index/", index_view, name="index"),
    path("task/detail/<int:pk>/", task_detail_view, name="task_detail"),
]
