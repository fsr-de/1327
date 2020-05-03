# from https://github.com/django-admin-bootstrapped/django-admin-bootstrapped/blob/master/django_admin_bootstrapped/templatetags/bootstrapped_goodies_tags.py
from django import template
from django.template import TemplateDoesNotExist
from django.template.loader import render_to_string


register = template.Library()


@register.simple_tag(takes_context=True)
def render_with_template_if_exist(context, template, fallback):
    text = fallback
    try:
        text = render_to_string(template, context)
    except (TemplateDoesNotExist, TypeError):
        pass
    return text


@register.filter(name='form_fieldset_column_width')
def form_fieldset_column_width(form):
    def max_line(fieldset):
        try:
            return max([len(list(line)) for line in fieldset])
        # This ValueError is for case that fieldset has no line.
        except ValueError:
            return 0

    try:
        width = max([max_line(fieldset) for fieldset in form])
        return 12 // width
    except ValueError:
        return 12


@register.simple_tag(takes_context=True)
def render_app_label(context, app, fallback=""):
    """ Render the application label.
    """
    try:
        text = app['app_label']
    except KeyError:
        text = fallback
    except TypeError:
        text = app
    return text


@register.simple_tag(takes_context=True)
def render_app_description(context, app, fallback="", template="/admin_app_description.html"):
    """ Render the application description using the default template name. If it cannot find a
        template matching the given path, fallback to the fallback argument.
    """
    try:
        template = app['app_label'] + template
        text = render_to_string(template, context)
    except TemplateDoesNotExist:
        text = fallback
    return text
