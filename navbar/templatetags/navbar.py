from django.template import Library
from django.conf import settings

def _getdefault(name, default=None):
    try:
        default = getattr(settings, name)
    except: pass
    return default

SHOW_DEPTH = _getdefault('NAVBAR_TREE_SHOW_DEPTH', -1)

numbers = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven',
           'eight', 'nine', 'ten', 'eleven', 'twelve', 'thirteen',
           'fourteen', 'fifteen', 'sixteen', 'seventeen', 'eightteen',
           'nineteen',]

_dig = numbers[1:10]
for ent in ['twenty', 'thirty', 'fourty', 'fifty', 'sixty', 'seventy',
            'eighty', 'ninety']:
    numbers.append(ent)
    numbers.extend(ent + "-" + num for num in _dig)

register = Library()

@register.filter
def cssnumber(num):
    """like humanize appnum but goes the full gambit from 0 to 99.
    Is not translated as this is intended for CSS use.
    0 : zero
    10: ten
    45: fourty-five

    use the filter tag if you want a translation...
    """
    return numbers[num]

@register.inclusion_tag('navbar/subtree.html')
def subtree(children, depth=0):
    """Process a sub part of the nav tree
    """
    return { 'subtree': children, 'depth': depth+1,
             'show_unselected': (SHOW_DEPTH == -1 or depth < SHOW_DEPTH),
             'level': numbers[depth+1] }


@register.inclusion_tag('navbar/tree.html', takes_context=True)
def navtree(context):
    """simpler helper so you dont need to do the include ;-)
    """
    return context

@register.inclusion_tag('navbar/navbar.html', takes_context=True)
def navbar(context):
    """simpler helper so you dont need to do the include ;-)
    """
    return context

@register.inclusion_tag('navbar/navbars.html', takes_context=True)
def navbars(context):
    """simpler helper so you dont need to do the include ;-)
    """
    return context
