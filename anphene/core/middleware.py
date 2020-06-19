from django.contrib.sites.models import Site
from django.utils import timezone
from django.utils.functional import SimpleLazyObject
from ..discounts.utils import fetch_discounts


def request_time(get_response):
    def _stamp_request(request):
        request.request_time = timezone.now()
        return get_response(request)

    return _stamp_request


def discounts(get_response):
    """Assign active discounts to `request.discounts`."""

    def _discounts_middleware(request):
        request.discounts = SimpleLazyObject(lambda: fetch_discounts(request.request_time))
        return get_response(request)

    return _discounts_middleware


def site(get_response):
    """Clear the Sites cache and assign the current site to `request.site`.

    By default django.contrib.sites caches Site instances at the module
    level. This leads to problems when updating Site instances, as it's
    required to restart all application servers in order to invalidate
    the cache. Using this middleware solves this problem.
    """

    def _get_site():
        Site.objects.clear_cache()
        return Site.objects.get_current()

    def _site_middleware(request):
        request.site = SimpleLazyObject(_get_site)
        return get_response(request)

    return _site_middleware
