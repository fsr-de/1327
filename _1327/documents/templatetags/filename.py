import os

from django import template
register = template.Library()

@register.filter
def filename(string):
    delimiter = os.sep
    return string.split(delimiter)[-1]
