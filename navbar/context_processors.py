from utils import get_navtree, get_navbar
from django.conf import settings

MAX_DEPTH = getattr(settings, 'NAVBAR_MAX_DEPTH', -1)
MARK_SELECTED = getattr(settings, 'NAVBAR_MARK_SELECTED', True)
SHOW_DEPTH = getattr(settings, 'NAVBAR_SHOW_DEPTH', -1)

CRUMBS_STRIP_ROOT = getattr(settings, 'NAVBAR_CRUMBS_STRIP_ROOT', True)
CRUMBS_HOME = getattr(settings, 'NAVBAR_CRUMBS_HOME', 'home')

def crumbs(request):
    """adds the path 'crumbs'
    crumbs have the format of:
    [ {'name': 'foo',  'path': '/foo'},
      {'name': 'bar',  'path': '/foo/bar'},
      {'name': 'bing', 'path': '/foo/bar/bing'} ]
    """
    rooturl = getattr(settings, 'ROOT_URL', '')
    assert(request.path.startswith(rooturl))
    if request.path != '/':
        # split the path into the names /name1/name2/name3
        crumb_names = request.path.strip('/').split('/')
    else:
        crumb_names = []
    crumbs = [ {'name': name, 'path': '/' + '/'.join(crumb_names[:ind+1]) + '/'}
                    for ind, name in enumerate(crumb_names) ]
    # complete the crumbs home setting, and pop off if there is no home set.
    if CRUMBS_HOME:
        home = { 'name': CRUMBS_HOME, 'path': '/' }
        crumbs.insert(0, home)

    # strip off the root (if there is one)
    if rooturl.strip('/') and CRUMBS_STRIP_ROOT:
        crumbs = crumbs[len(rooturl.strip('/').split('/')):]
        if CRUMBS_HOME:
            crumbs[0]['name'] = CRUMBS_HOME
    return { 'crumbs': crumbs }

def _mark_selected(path, byurl):
    """process the tree (flattened and sorted by url) to mark the entries
    selected which appear on the path, as well as their parent entries.
    """
    clear = []
    check = path.startswith
    for url, val in byurl:
        pt = val['path_type']
        if pt == 'N': continue
        elif pt != 'A' and path != url: continue
        elif check(url):
            while val:
                if val['selected']: break
                if (val['path_type'] == 'N' or (val['path_type'] == 'E' and
                        path != val['url'])): clear.append(val)
                val['selected'] = True
                val = val['parent']
    for ent in clear: ent['selected'] = False

def navbar(request):
    """adds the variable 'navbar' to the context"
    """
    navbar = get_navbar(request.user)
    if MARK_SELECTED:
        base = {'selected': False, 'parent': None}
        navbar = navbar.values()
        for e in navbar: e.update(base)
        byurl = [ (e['url'], e) for e in
                    sorted(navbar, key=lambda x: x['url'], reverse=True) ]
        _mark_selected(request.path, byurl)
    return { 'navbar': navbar }

def navbars(request):
    """adds the variable 'navbars' to the context"
    """
    nav    = get_navtree(request.user, MAX_DEPTH)
    navbar = nav['tree']
    _mark_selected(request.path, nav['byurl'])
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
    if MARK_SELECTED: _mark_selected(request.path, navbar['byurl'])
    return {'navtree':  navbar['tree']}
