from django.urls import path

from core.views.github import github_webhook, health_check

urlpatterns = [
    path("webhook", github_webhook, name="github_webhook"),
    path("h/", health_check, name="health_check"),
]
