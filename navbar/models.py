"""NavBar models for building and managing dynamic site navigation
"""
from django.db import models
from django.conf import settings
from django.contrib.auth.models import Group
from django.core.cache import cache
from django.db.models.query import Q
from django.utils.translation import ugettext_lazy as _

USER_TYPE_CHOICES = [
    ('A', _('Anonymous')),
    ('L', _('Logged In')),
    ('S', _('Staff')),
    ('X', _('Superuser')),
]

SELECTION_TYPE_CHOICES = [
    ('N', _('Never')),
    ('E', _('Exact')),
    ('P', _('ExactOrParent')),
    ('A', _('OnPathOrParent (default)'))
]

class NavBarRootManager(models.Manager):
    def get_query_set(self):
        all = super(NavBarRootManager, self).get_query_set()
        return all.filter(parent__isnull=True)


class NavBarEntry(models.Model):
    name   = models.CharField(max_length=50,
                              help_text=_("text seen in the menu"))
    title  = models.CharField(max_length=50, blank=True,
                              help_text=_("mouse hover description"))
    url    = models.CharField(max_length=200)
    order  = models.IntegerField(default=0)
    parent = models.ForeignKey('self', related_name='children',
                               blank=True, null=True)

    ## advanced permissions
    path_type = models.CharField(_('path match type'), max_length=1,
                                 choices=SELECTION_TYPE_CHOICES, default='A',
                                 help_text=_("Control how this element is "
                                             "marked 'selected' based on the "
                                             "request path."))
    user_type = models.CharField(_('user login type'), max_length=1,
                                 choices=USER_TYPE_CHOICES,
                                 default=USER_TYPE_CHOICES[0][0])
    groups    = models.ManyToManyField(Group, null=True, blank=True)

    objects = models.Manager()
    top     = NavBarRootManager()

    class Meta:
        verbose_name = 'navigation bar element'
        verbose_name_plural = 'navigation bar elements'
        #order_with_respect_to = 'parent' # doesn't woth with self relations
        ordering = ('parent__id', 'order', 'name', 'url')

    def __unicode__(self):
        return self.name

    def save(self):
        cache.delete('site_navtree')
        cache.delete('site_navtree_super')
        return super(NavBarEntry, self).save()

def Qperm(user=None):
    exQ = Q()
    if user is None or user.is_anonymous():
        exQ = Q(user_type__exact = 'A') & Q(
            groups__isnull=True)
    elif user.is_superuser:
        pass
    elif user.is_staff:
        exQ = (Q(user_type__exact = 'A') | Q(user_type__exact = 'L') |
               Q(user_type__exact = 'S')) & (
                    Q(groups__in=user.groups.all()) | Q(groups__isnull=True))
    else:
        exQ = (Q(user_type__exact = 'A') | Q(user_type__exact = 'L')) & (
                    Q(groups__in=user.groups.all()) | Q(groups__isnull=True))
    return exQ

def generate_navtree(user=None, maxdepth=-1):
    if maxdepth == 0: return [] ## silly...
    permQ = Qperm(user)
    urls = {}
    def navent(ent, invdepth, parent):
        current = {'name': ent.name, 'title': ent.title, 'url': ent.url,
                   'selected': False, 'path_type': ent.path_type, 'parent': parent}
        urls.setdefault(ent.url, current)
        current['children'] = navlevel(ent.children, invdepth-1, current)
        return current
    def navlevel(base, invdepth, parent=None):
        if invdepth == 0 : return []
        return [ navent(ent, invdepth, parent)
                        for ent in base.filter(permQ).distinct() ]
    tree = navlevel(NavBarEntry.top, maxdepth)
    urls = sorted(urls.iteritems(), key=lambda x: x[0], reverse=True)
    return {'tree': tree, 'byurl': urls}

def get_navtree(user=None, maxdepth=-1):
    cachename = 'site_navtree'
    timeout = 60*60*24
    if user is not None and not user.is_anonymous():
        if user.is_superuser:
            cachename = 'site_navtree_super'
        else:
            cachename = 'site_navtree_' + str(user.id)
            timeout = 60*15
    data = cache.get(cachename)
    if data is None:
        data = generate_navtree(user, maxdepth)
        cache.set(cachename, data, timeout)
    return data

def get_navbar(user=None):
    return NavBarEntry.top.filter(Qperm(user))
