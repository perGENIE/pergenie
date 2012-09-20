from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()


"""
to use this sctipt, put this in .html

{% load extras %}}

"""


# Django 'set variable' support
# from http://www.soyoucode.com/2011/set-variable-django-template

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
def space2underbar(s):
    return s.replace(' ', '_')


# @register.filter
# def keyvalue(dict, key):
#     return dict[key]['genotype']
