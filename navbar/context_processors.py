from models import get_navtree, get_navbar
from django.conf import settings

def _getdefault(name, default=None):
    try:
        default = getattr(settings, name)
    except: pass
    return default

MAX_DEPTH = _getdefault('NAVBAR_TREE_MAX_DEPTH', -1)
MARK_SELECTED = _getdefault('NAVBAR_TREE_MARK_SELECTED', True)
SHOW_DEPTH = _getdefault('NAVBAR_TREE_SHOW_DEPTH', -1)

def crumbs(request):
    """adds the path 'crumbs'
    crumbs have the format of:
    [ {'name': 'foo', 'path': 'foo'},
      {'name': 'bar', 'path': 'foo/bar'},
      {'name': 'bing', 'path': 'foo/bar/bing'} ]
    """
    rooturl = getattr(settings, 'ROOT_URL')
    crumb_names = request.path[len(rooturl):].split('/')
    crumb_names.insert(0, rooturl.strip('/'))
    crumbs = [ {'name': name, 'path': '/'+'/'.join(crumb_names[:ind+1])+'/'}
                    for ind, name in enumerate(crumb_names) if name ]
    crumbs[0]['name'] = 'home'
    return { 'crumbs': crumbs }

def navbar(request):
    """adds the variable 'navbar' to the context"
    """
    navbar = get_navbar(request.user)
    for ent in navbar: ent.selected = request.path.startswith(ent.url)
    return { 'navbar': navbar }

def navbars(request):
    """adds the variable 'navbar' to the context"
    """
    nav    = get_navtree(request.user, MAX_DEPTH)
    navbar = nav['tree']
    byurl  = nav['byurl']
    check = request.path.startswith
    for url, val in byurl.iteritems():
        if check(url):
            while val:
                if val['selected']: break
                val['selected'] = True
                val = val['parent']
    navbars = [ navbar ]
    found = True
    while navbar and found:
        found = False
        for ent in navbar:
            if ent['selected']:
                navbar = ent['children']
                if navbar: navbars.append(navbar)
                found = True
                break;
    if SHOW_DEPTH > len(navbars):
        navbars += [[]]*(SHOW_DEPTH - len(navbars))
    return { 'navbars': navbars }

def navtree(request):
    """adds the variable 'navtree' to the context:
        [ { 'name': 'about', 'title': 'All about the site',
            'url': '/about/', 'children': [] },
          { 'name': 'news', 'title': 'Latest News',
            'url': '/news/', 'children':
            [ { 'name': 'August', 'title': 'August Archive',
                'url': '/news/aug/', 'children': [] }, ]]
    """
    navbar = get_navtree(request.user, MAX_DEPTH)
    if MARK_SELECTED:
        check = request.path.startswith
        for url, val in navbar['byurl'].iteritems():
            if check(url):
                while val:
                    if val['selected']: break
                    val['selected'] = True
                    val = val['parent']
    return {'navtree':  navbar['tree']}
