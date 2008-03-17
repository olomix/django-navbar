"""NavBar models for building and managing dynamic site navigation
"""
from django.db import models
from django.conf import settings
from django.contrib.auth.models import Group
from django.core.validators import ValidationError
from django.core.cache import cache
from django.db.models.query import Q, QNot
from pycon.core import *
from cPickle import dumps, loads, HIGHEST_PROTOCOL
import re

USER_TYPE_CHOICES = Choices([
    ('A', 'Anonymous'),
    ('L', 'Logged In'),
    ('S', 'Staff'),
    ('X', 'Superuser'),
])

url_re = re.compile(r'^(https?:/)?/\S+$')

def IsNotCircular(field_data, all_data):
    if 'id' not in all_data or all_data['id'] is None or not all_data['parent']:
        return
    cid = int(all_data['id'])
    pid = int(all_data['parent'])
    try:
        while pid:
            parent = NavBarEntry.objects.get(pk=pid)
            pid = parent.parent_id
            if pid is None: return
            if pid == cid:
                raise ValidationError(u"Creates a cyclical reference.")
    except NavBarEntry.DoesNotExist:
        raise ValidationError("Could not find parent: " + str(pid) +
                              " Corrupt DB?")

def isValidLocalOrServerURL(field_data, all_data):
    if not url_re.search(field_data):
        raise ValidationError(u"A valid URL is required.")
    ## RED_FLAG: add signals based local check (from request object)
    if field_data.startswith('http'):
        import urllib2
        try:
            from django.conf import settings
            URL_VALIDATOR_USER_AGENT = settings.URL_VALIDATOR_USER_AGENT
        except (ImportError, EnvironmentError):
            # It's OK if Django settings aren't configured.
            URL_VALIDATOR_USER_AGENT = 'Django (http://www.djangoproject.com/)'
        headers = {
            "Accept": "text/xml,application/xml,application/xhtml+xml,"
                      "text/html;q=0.9,text/plain;q=0.8,image/png,*/*;q=0.5",
            "Accept-Language": "en-us,en;q=0.5",
            "Accept-Charset": "ISO-8859-1,utf-8;q=0.7,*;q=0.7",
            "Connection": "close",
            "User-Agent": URL_VALIDATOR_USER_AGENT,
        }
        try:
            req = urllib2.Request(field_data, None, headers)
            u = urllib2.urlopen(req)
        except ValueError:
            raise ValidationError(u'Enter a valid URL.')
        except: # urllib2.URLError, httplib.InvalidURL, etc.
            raise ValidationError(u'This URL appears to be a broken link.')

class NavBarRootManager(models.Manager):
    def get_query_set(self):
        all = super(NavBarRootManager, self).get_query_set()
        return all.filter(parent__isnull=True)


class NavBarEntry(models.Model):
    name   = models.CharField(max_length=50,
                              help_text="text seen in the menu")
    title  = models.CharField(max_length=50, blank=True,
                              help_text="mouse hover description")
    url    = models.CharField(max_length=200, validator_list=[
                                                    isValidLocalOrServerURL])
    order  = models.IntegerField(default=0)
    parent = models.ForeignKey('self', related_name='children',
                               blank=True, null=True,
                               validator_list=[IsNotCircular])

    ## advanced permissions
    user_type = models.CharField('user login type', maxlength=1,
                                 choices=USER_TYPE_CHOICES,
                                 default=USER_TYPE_CHOICES.default)
    groups    = models.ManyToManyField(Group, null=True, blank=True,
                                       filter_interface = models.HORIZONTAL)

    objects = models.Manager()
    top     = NavBarRootManager()

    class Meta:
        verbose_name = 'navigation bar element'
        verbose_name_plural = 'navigation bar elements'
        #order_with_respect_to = 'parent' # doesn't woth with self relations
        ordering = ('parent', 'order', 'name', 'url')
    class Admin:
        fields = (
            (None, {'fields': ('name', 'title', 'url', 'order', 'parent')}),
            ('Advanced Permissions', {'classes': 'collapse',
                             'fields': ('user_type', 'groups', )}),
        )
        list_filter = ('parent',)
        list_display = ('name', 'url', 'order', 'parent')
        search_fields = ('url', 'name', 'title')

    def __unicode__(self):
        return self.name

    def save(self):
        cache.delete('site_navtree')
        cache.delete('site_navtree_super')
        return super(NavBarEntry, self).save(self)

def Qperm(user=None):
    exQ = Q()
    if user is None or user.is_anonymous():
        exQ = Q(user_type__exact = USER_TYPE_CHOICES.find('Anonymous')) & Q(
            groups__isnull=True)
    elif user.is_superuser:
        pass
    elif user.is_staff:
        exQ = (Q(user_type__exact = USER_TYPE_CHOICES.find('Anonymous')) |
               Q(user_type__exact = USER_TYPE_CHOICES.find('Logged In')) |
               Q(user_type__exact = USER_TYPE_CHOICES.find('Staff'))) & (
                    Q(groups__in=user.groups.all()) | Q(groups__isnull=True))
    else:
        exQ = (Q(user_type__exact = USER_TYPE_CHOICES.find('Anonymous')) |
               Q(user_type__exact = USER_TYPE_CHOICES.find('Logged In'))) & (
                    Q(groups__in=user.groups.all()) | Q(groups__isnull=True))
    return exQ

def generate_navtree(user=None, maxdepth=-1):
    if maxdepth == 0: return [] ## silly...
    permQ = Qperm(user)
    urls = {}
    def navent(ent, invdepth, parent):
        current = {'name': ent.name, 'title': ent.title, 'url': ent.url,
                   'selected': False, 'parent': parent}
        urls.setdefault(ent.url, current)
        current['children'] = navlevel(ent.children, invdepth-1, current)
        return current
    def navlevel(base, invdepth, parent=None):
        if invdepth == 0 : return []
        return [ navent(ent, invdepth, parent)
                        for ent in base.filter(permQ).distinct() ]
    tree = navlevel(NavBarEntry.top, maxdepth)
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
