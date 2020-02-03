from __future__ import unicode_literals

from django.conf.urls import url

from reviewbotext.views import (ConfigureUserView,
                                ConfigureView,
                                WorkerStatusView)


urlpatterns = [
    url(r'^$', ConfigureView.as_view(), name='reviewbot-configure'),
    url(r'^user/$', ConfigureUserView.as_view(),
        name='reviewbot-configure-user'),
    url(r'^worker-status/$', WorkerStatusView.as_view(),
        name='reviewbot-worker-status'),
]
