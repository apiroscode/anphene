import json

from debug_toolbar.middleware import DebugToolbarMiddleware as BaseMiddleware
from debug_toolbar.toolbar import DebugToolbar
from django.conf import settings
from django.template.loader import render_to_string
from graphiql_debug_toolbar.middleware import get_payload, set_content_length
from graphiql_debug_toolbar.serializers import CallableJSONEncoder

from .views import GraphQLView

__all__ = ["DebugToolbarMiddleware"]


def show_toolbar(request):
    """
    Default function to determine whether to show the toolbar on a given page.
    """
    if request.META.get("REMOTE_ADDR", None) not in settings.INTERNAL_IPS:
        return False
    if any([str(port) in request.META.get("HTTP_ORIGIN", "") for port in settings.CLIENT_PORT]):
        return False

    return bool(settings.DEBUG)


class DebugToolbarMiddleware(BaseMiddleware):
    def process_view(self, request, view_func, *args):
        if hasattr(view_func, "view_class") and issubclass(view_func.view_class, GraphQLView):
            request._graphql_view = True

    def __call__(self, request):
        if not show_toolbar(request) or request.is_ajax():
            return self.get_response(request)

        if request.content_type != "application/json":
            response = super().__call__(request)
            content_type = response.get("Content-Type", "").split(";")[0]
            if content_type == "text/html":
                template = render_to_string("graphiql_debug_toolbar/base.html")
                response.write(template)
                set_content_length(response)
            return response

        toolbar = DebugToolbar(request, self.get_response)

        for panel in toolbar.enabled_panels:
            panel.enable_instrumentation()
        try:
            response = toolbar.process_request(request)
        finally:
            for panel in reversed(toolbar.enabled_panels):
                panel.disable_instrumentation()

        response = self.generate_server_timing_header(response, toolbar.enabled_panels)
        payload = get_payload(request, response, toolbar)
        response.content = json.dumps(payload, cls=CallableJSONEncoder)
        set_content_length(response)
        return response
