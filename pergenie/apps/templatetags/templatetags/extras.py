# -*- coding: utf-8 -*-

"""
To use filters bellow, put `{% load extras %}` in templates.
"""

from django import template
from django.template.defaultfilters import stringfilter  # 第一引数に文字列しかとらない
from django.conf import settings
import math

register = template.Library()


"""
Django 'set variable' support
from http://www.soyoucode.com/2011/set-variable-django-template
"""

class SetVarNode(template.Node):
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


# from xml.sax.saxutils import unescape, escape
# @register.filter
# @stringfilter
# def unescape_html(s):
#     return unescape(s)



@register.filter
@stringfilter
def space2underbar(s):
    return s.replace(' ', '_')

@register.filter
@stringfilter
def underbar2space(s):
    return s.replace('_', ' ')


#
@register.filter
def keyvalue(dict, key):
    return dict[key]

#
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

@stringfilter
@register.filter
def file_format(s):
    # e.g.: map `vcf_whole_genome` to `VCF (Whole Genome)`
    return dict((x[0], x[2]) for x in settings.FILEFORMATS)[s]

@stringfilter
@register.filter
def demouser_format(s):
    if s.startswith(settings.DEMO_USER_ID):
        s = settings.DEMO_USER_ID

    return s

# @stringfilter
# @register.filter
# def rm_newlines(s):
#     return ''.join(s.splitlines())

# @register.filter
# def one_value(dict):
#     return dict.get(dict.keys()[0])
@register.filter
def dict_index(dict, index):
    return dict.get(dict.keys()[index])

@register.filter
@stringfilter
def hide_None(s):
    return s.replace('None', '')

@register.filter
@stringfilter
def is_in_installed_my_apps(s):
    installed_my_apps = [x[5:] for x in settings.INSTALLED_APPS if x.startswith('apps.')]
    return s in installed_my_apps
