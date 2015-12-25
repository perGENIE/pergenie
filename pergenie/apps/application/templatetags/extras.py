"""
To use filters bellow, put `{% load extras %}` in templates.
"""

import math

from django import template
from django.template.defaultfilters import stringfilter  # only expects a string as the first argument
from django.conf import settings

from lib.utils.population import POPULATION_MAP

register = template.Library()

class SetVarNode(template.Node):
    """Django 'set variable' support

    See http://www.soyoucode.com/2011/set-variable-django-template
    """

    def __init__(self, var_name, var_value):
        self._var_name = var_name
        self._var_value = var_value

    def render(self, context):
        try:
            value = template.Variable(self._var_value).resolve(context)
        except template.VariableDoesNotExist:
            value = ''

        context[self._var_name] = value
        return u''

@register.tag('set')
def set_var(parser, token):
    parts = token.split_contents()

    if len(parts) < 4:
        msg = "'set' tag must be of the form: {% set <var_name>  = <var_value> %}"
        raise template.TemplateSyntaxError(msg)

    return SetVarNode(parts[1], parts[3])

@register.filter
@stringfilter
def limit(s, length):
    if len(s) <= int(length):
        return s
    else:
        return s[:int(length)] + '...'

@register.filter
def keyvalue(dict, key):
    return dict[key]

@register.filter
def listvalue(list, index):
    return list[index]

@register.filter
def pow10(float, value):
    return round(10**value, 3)

@stringfilter
@register.filter
def abs(s):
    #
    try:
        value = float(s)
    except ValueError:
        return s

    return math.fabs(value)

def dict_index(dict, index):
    return dict.get(dict.keys()[index])

@register.filter
@stringfilter
def hide_None(s):
    return s.replace('None', '')

@register.filter
@stringfilter
def is_in_installed_apps(s):
    installed_apps = [x for x in settings.INSTALLED_APPS if x.startswith('apps.')]
    return 'apps.' + s in installed_apps

@register.filter
@stringfilter
def population_display_name(s):
    return POPULATION_MAP.get(s, '.')
