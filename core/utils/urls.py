import socket
from urllib.parse import urljoin, urlparse

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from django.http.request import split_domain_port, validate_host
from django.utils.encoding import iri_to_uri


def is_valid_ipv4(ip: str) -> bool:
    """Check whether the passed IP is a valid V4 IP address."""
    try:
        socket.inet_pton(socket.AF_INET, ip)
    except socket.error:
        return False
    return True


def is_valid_ipv6(ip: str) -> bool:
    """Check whether the passed IP is a valid V6 IP address."""
    try:
        socket.inet_pton(socket.AF_INET6, ip)
    except socket.error:
        return False
    return True


def validate_storefront_url(url):
    """Validate the storefront URL.

    Raise ValidationError if URL isn't in RFC 1808 format
    or it isn't allowed by ALLOWED_CLIENT_HOSTS in settings.
    """
    try:
        parsed_url = urlparse(url)
        domain, _ = split_domain_port(parsed_url.netloc)
        if not parsed_url.netloc:
            raise ValidationError("Invalid URL. Please check if URL is in RFC 1808 format.")
    except ValueError as error:
        raise ValidationError(error)
    if not validate_host(domain, settings.ALLOWED_CLIENT_HOSTS):
        error_message = (
            f"{domain or url} is not allowed. Please check "
            "`ALLOWED_CLIENT_HOSTS` configuration."
        )
        raise ValidationError(error_message)


def build_absolute_uri(location):
    host = Site.objects.get_current().domain
    protocol = "https" if settings.ENABLE_SSL else "http"
    current_uri = "%s://%s" % (protocol, host)
    location = urljoin(current_uri, location)
    return iri_to_uri(location)
