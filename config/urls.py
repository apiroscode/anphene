from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.http import JsonResponse
from django.urls import include, path
from django.views import defaults as default_views
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie, get_token

from anphene.core.api import schema
from core.views import GraphQLView


@ensure_csrf_cookie
def init(request):
    return JsonResponse({"result": get_token(request)})


if settings.DEBUG:
    graph_url = path("graphql/", csrf_exempt(GraphQLView.as_view(schema=schema)), name="api")
else:
    graph_url = path("graphql/", GraphQLView.as_view(schema=schema), name="api")

urlpatterns = [graph_url, path("init/", init)] + static(
    settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
)


if settings.DEBUG:
    # Static file serving when using Gunicorn + Uvicorn for local web socket development
    urlpatterns += staticfiles_urlpatterns()
    # This allows the error pages to be debugged during development, just visit
    # these url in browser to see how these error pages look like.
    urlpatterns += [
        path("400/", default_views.bad_request, kwargs={"exception": Exception("Bad Request!")},),
        path(
            "403/",
            default_views.permission_denied,
            kwargs={"exception": Exception("Permission Denied")},
        ),
        path(
            "404/",
            default_views.page_not_found,
            kwargs={"exception": Exception("Page not Found")},
        ),
        path("500/", default_views.server_error),
    ]
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
