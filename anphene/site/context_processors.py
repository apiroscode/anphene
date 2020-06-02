from django.contrib.sites.shortcuts import get_current_site


def site(request):
    """Add site settings to the context under the 'site' key."""
    site = get_current_site(request)

    return {"site": site}
