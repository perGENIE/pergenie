# -*- coding: utf-8 -*-

"""
To use filters bellow, put `{% load extras %}}` in templates.
"""

from django import template
from django.template.defaultfilters import stringfilter  # 第一引数に文字列しかとらない

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
def file_format(s):
    maps = {'andme': '23andMe',
            'vcf_whole_genome': 'VCF (Whole Genome)',
            'vcf_exome_truseq': 'VCF (TruSeq Exome)'}

    return maps[s]
