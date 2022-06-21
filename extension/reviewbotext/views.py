from __future__ import unicode_literals

import json

import six
from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.http import (HttpResponse,
                         HttpResponseBadRequest,
                         HttpResponseForbidden)
from django.shortcuts import get_object_or_404, render
from django.views.generic import TemplateView, View
from djblets.avatars.services import URLAvatarService
from djblets.db.query import get_object_or_none
from djblets.siteconfig.models import SiteConfiguration
from reviewboard.admin.server import get_server_url
from reviewboard.avatars import avatar_services
from reviewboard.site.urlresolvers import local_site_reverse

from reviewbotext.extension import ReviewBotExtension


def _serialize_user(request, user):
    """Serialize a user into a JSON-encodable format.

    Args:
        request (django.http.HttpRequest):
            The HTTP request.

        user (django.contrib.auth.models.User):
            The user to serialize.

    Returns:
        dict:
        A dictionary of data to be encoded and sent back to the client.
    """
    if user:
        service = avatar_services.for_user(user)

        if service:
            avatar_url = service.get_avatar_urls(request, user, 48)['1x']
        else:
            avatar_url = None

        return {
            'avatar_url': avatar_url,
            'id': user.id,
            'fullname': user.get_full_name(),
            'username': user.username,
        }
    else:
        return None


class ConfigureView(TemplateView):
    """The basic "Configure" page for Review Bot."""

    template_name = 'reviewbot/configure.html'

    def get(self, request):
        """Render and return the admin page.

        Args:
            request (django.http.HttpRequest):
                The HTTP request.

        Returns:
            django.http.HttpResponse:
            The response.
        """
        if not request.user.is_superuser:
            # TODO: Once we move to Django 1.9+, we can switch to the new
            # access mixin methods instead of testing this ourselves. Here and
            # below in the other views in this file.
            return HttpResponseForbidden()

        return super(ConfigureView, self).get(request)

    def post(self, request):
        """Save the extension configuration.

        Args:
            request (django.http.HttpRequest):
                The HTTP request, including POSTed data.

        Returns:
            django.http.HttpResponse:
            The response. The body of the response is a JSON-encoded blob which
            indicates success or failure, and in the success case, includes the
            the current configuration.
        """
        if not request.user.is_superuser:
            return HttpResponseForbidden()

        extension = ReviewBotExtension.instance
        should_save = False
        new_user = request.POST.get('reviewbot_user')

        if new_user:
            try:
                user = User.objects.get(pk=new_user)
            except User.DoesNotExist:
                # TODO: return which field was invalid
                return HttpResponseBadRequest(
                    json.dumps({
                        'result': 'error',
                        'field': 'user',
                        'error': 'The specified user does not exist.',
                    }),
                    content_type='application/json')

            extension.settings['user'] = user.pk
            should_save = True
        else:
            user = get_object_or_none(User, pk=extension.settings.get('user'))

        if 'reviewbot_broker_url' in request.POST:
            broker_url = request.POST['reviewbot_broker_url']
            extension.settings['broker_url'] = broker_url
            should_save = True
        else:
            broker_url = extension.settings.get('broker_url', '')

        if should_save:
            extension.settings.save()

        return HttpResponse(
            json.dumps({
                'result': 'success',
                'broker_url': broker_url,
                'user': _serialize_user(request, user),
            }),
            content_type='application/json')

    def get_context_data(self, **kwargs):
        """Return context data for the template.

        This will provide the extension information, broker URL, utility
        URLs, and the Review Bot user information.

        Args:
            **kwargs (dict):
                Additional keyword arguments passed when dispatching.

        Returns:
            dict:
            The context data for the page.
        """
        request = self.request
        extension = ReviewBotExtension.instance

        extension_config_attrs = {
            'brokerURL': extension.settings.get('broker_url'),
        }

        # Add information on the Review Bot User entry.
        user = get_object_or_none(User, pk=extension.settings.get('user'))

        if user:
            extension_config_attrs['user'] = _serialize_user(request, user)

        return dict(super(ConfigureView, self).get_context_data(**kwargs), **{
            'extension': extension,
            'extension_config_attrs': extension_config_attrs,
            'extension_config_options': {
                'integrationConfigURL': local_site_reverse(
                    'integration-list',
                    request=request),
                'userConfigURL': local_site_reverse(
                    'reviewbot-configure-user',
                    request=request),
                'workerStatusURL': local_site_reverse(
                    'reviewbot-worker-status',
                    request=request),
            },
        })


class ConfigureUserView(View):
    """An endpoint for setting the user for Review Bot."""

    def get(self, request):
        """Return the configured user.

        Args:
            request (django.http.HttpRequest):
                The HTTP request.

        Returns:
            django.http.HttpResponse:
            A response containing the currently-configured user.
        """
        if not request.user.is_superuser:
            return HttpResponseForbidden()

        extension = ReviewBotExtension.instance
        user = get_object_or_404(User, pk=extension.settings.get('user'))

        return HttpResponse(json.dumps(_serialize_user(request, user)),
                            content_type='application/json')

    def post(self, request):
        """Create a new user for Review Bot.

        Args:
            request (django.http.HttpRequest):
                The HTTP request.

        Returns:
            django.http.HttpResponse:
            A response containing the newly-configured user.
        """
        if not request.user.is_superuser:
            return self.get_no_access_error(request)

        siteconfig = SiteConfiguration.objects.get_current()
        noreply_email = siteconfig.get('mail_default_from')

        extension = ReviewBotExtension.instance

        try:
            with transaction.atomic():
                user = User.objects.create(username='reviewbot',
                                           email=noreply_email,
                                           first_name='Review',
                                           last_name='Bot')

                profile = user.get_profile()
                profile.should_send_email = False
                profile.save(update_fields=('should_send_email',))

                avatar_service = avatar_services.get_avatar_service(
                    URLAvatarService.avatar_service_id)
                extension = ReviewBotExtension.instance
                avatar_service.setup(
                    user,
                    {
                        '1x': extension.get_static_url(
                            'images/reviewbot.png'),
                        '2x': extension.get_static_url(
                            'images/reviewbot@2x.png'),
                    })
        except IntegrityError:
            return HttpResponseBadRequest()

        extension.settings['user'] = user.pk
        extension.settings.save()

        return HttpResponse(json.dumps(_serialize_user(request, user)),
                            content_type='application/json')


class WorkerStatusView(View):
    """An "API" to get worker status.

    This view is an internal API to query the workers and return their status.
    """

    def get(self, request):
        """Query workers and return their status.

        Args:
            request (django.http.HttpRequest):
                The HTTP request.

        Returns:
            django.http.HttpResponse:
            The response.
        """
        extension = ReviewBotExtension.instance
        response = {}

        if extension.is_configured:
            try:
                payload = {
                    'session': extension.login_user(),
                    'url': get_server_url(),
                }
                reply = extension.celery.control.broadcast('update_tools_list',
                                                           payload=payload,
                                                           reply=True,
                                                           timeout=10)

                state = 'success'
                error = None
                hosts = []

                for item in reply:
                    for worker_host, data in six.iteritems(item):
                        worker_status = data.get('status')

                        if worker_status == 'ok':
                            hosts.append({
                                'hostname': worker_host.split('@', 1)[1],
                                'tools': data['tools'],
                            })
                        elif worker_status == 'error':
                            state = 'error'
                            error = (
                                'Error from %s: %s'
                                % (worker_host, data['error'])
                            )
                            break
                        else:
                            state = 'error'
                            error = (
                                "Unexpected result when querying worker "
                                "status for %s. Please check the worker's "
                                "logs for information."
                                % worker_host
                            )
                            break

                response = {
                    'state': state,
                }

                if state == 'success':
                    response['hosts'] = hosts
                else:
                    response['error'] = error
            except IOError as e:
                response = {
                    'state': 'error',
                    'error': 'Unable to connect to broker: %s' % e,
                }
        else:
            response = {
                'state': 'error',
                'error': 'Review Bot is not yet configured.',
            }

        return HttpResponse(json.dumps(response),
                            content_type='application/json')
