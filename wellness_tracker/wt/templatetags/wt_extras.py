import json as json_orig
from django import template
from django.utils.safestring import mark_safe

from wt.models import is_physician as model_is_physician
from wt.models import is_significant_other as model_is_significant_other

register = template.Library()

def date_handler(obj):
    return obj.isoformat() if hasattr(obj, 'isoformat') else obj

@register.filter
def classname(obj, arg=None):
    classname = obj.__class__.__name__.lower()
    if arg:
        if arg.lower() == classname:
            return True
        else:
            return False
    else:
        return classname

@register.filter
def is_physician(user):
    return model_is_physician(user)

@register.filter
def json(value):
    return mark_safe(json_orig.dumps(value, default=date_handler))

@register.filter
def is_significant_other(user):
    return model_is_significant_other(user)
