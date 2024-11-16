from django import template
from django.urls import resolve

register = template.Library()


@register.simple_tag
def is_active_tab(request, url_name):
    """Determine if the given URL name matches the current request's URL name.

    Args:
        request: The current HTTP request
        url_name: The name of the URL to check against

    Returns:
        bool: True if the current URL matches the given URL name
    """
    try:
        return resolve(request.path_info).url_name == url_name
    except AttributeError:
        return False
