"""NavBar models for building and managing dynamic site navigation
"""
from django.db import models
from django.conf import settings
from django.contrib.auth.models import Group
from django.core.cache.backends.locmem import CacheClass as LocalMemCache
from django.utils.translation import ugettext_lazy as _

NAVBAR_LOCAL_CACHE_PARAMS = getattr(settings, 'NAVBAR_LOCAL_CACHE_PARAMS',
                                     {'cull_frequency': 4,
                                      'max_entries': 3000,
                                     'timeout': 60*60*24*3, # 3 days
                                     })

NAVBAR_USE_LOCAL_CACHE = getattr(settings, 'NAVBAR_USE_LOCAL_CACHE', True)
if NAVBAR_USE_LOCAL_CACHE:
    cache = LocalMemCache('localhost', NAVBAR_LOCAL_CACHE_PARAMS)
else:
    from django.core.cache import cache

USER_TYPE_CHOICES = [
    ('E', _('Everybody')),
    ('A', _('Anonymous Only')),
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
        global cache
        if not NAVBAR_USE_LOCAL_CACHE:
            cache.delete('site_navtree')
            cache.delete('site_navtree_super')
        else:
            oldcache = cache
            cache = LocalMemCache('localhost', NAVBAR_LOCAL_CACHE_PARAMS)
            del oldcache
        return super(NavBarEntry, self).save()

    def delete(self, *args, **kwdargs):
        global cache
        if not NAVBAR_USE_LOCAL_CACHE:
            cache.delete('site_navtree')
            cache.delete('site_navtree_super')
        else:
            oldcache = cache
            cache = LocalMemCache('localhost', NAVBAR_LOCAL_CACHE_PARAMS)
            del oldcache
        return super(NavBarEntry, self).delete(*args, **kwdargs)
