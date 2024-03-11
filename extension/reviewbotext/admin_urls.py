"""Admin URL definitions for Review Bot."""

from django.urls import path

from reviewbotext.views import (ConfigureUserView,
                                ConfigureView,
                                WorkerStatusView)


urlpatterns = [
    path('', ConfigureView.as_view(), name='reviewbot-configure'),
    path('user/', ConfigureUserView.as_view(),
         name='reviewbot-configure-user'),
    path('worker-status/', WorkerStatusView.as_view(),
         name='reviewbot-worker-status'),
]
