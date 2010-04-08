from django.contrib import admin
from django import forms
from navbar.models import NavBarEntry
import re, urllib2

url_re = re.compile(r'^(https?://([a-zA-Z0-9]+\.)+[a-zA-Z0-9]+([:@][a-zA-Z0-9@%-_\.]){0,2})?/\S*$')

class NavBarEntryAdminForm(forms.ModelForm):
    class Meta:
        model = NavBarEntry

    def clean_url(self):
        url = self.cleaned_data["url"].strip()
        if not url_re.search(url):
            raise forms.ValidationError("A valid URL is required.")
        ## RED_FLAG: add signals based local check (from request object)
        if url.startswith('http'):
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
                req = urllib2.Request(url, None, headers)
                u = urllib2.urlopen(req)
            except ValueError:
                raise forms.ValidationError(u'Enter a valid URL.')
            except: # urllib2.URLError, httplib.InvalidURL, etc.
                raise forms.ValidationError(u'This URL appears to be a broken link.')
        return url

        def clean_parent(self):
            cid = self.instance.pk
            parent = self.cleaned_data["parent"]
            try:
                pids = []
                while parent:
                    parent = NavBarEntry.objects.get(pk=parent.id)
                    if parent.id in pids:
                        raise forms.ValidationError(u"Creates a cyclical reference.")
                    elif parent.parent != None:
                        parent = parent.parent
                    else: break
                    pids.append(parent.id)
            except NavBarEntry.DoesNotExist:
                raise forms.ValidationError("Could not find parent: " + str(pid) +
                                            " Corrupt DB?")
            return parent

class NavBarEntryAdmin(admin.ModelAdmin):
        form = NavBarEntryAdminForm
        fieldsets = (
            (None, {'fields': ('name', 'title', 'url', 'order', 'parent')}),
            ('Advanced Permissions', {'classes': ('collapse',),
                             'fields': ('path_type', 'user_type', 'groups', )}),
        )
        list_filter = ('parent',)
        list_display = ('name', 'url', 'order', 'parent')
        search_fields = ('url', 'name', 'title')
        filter_horizontal = ("groups",)

admin.site.register(NavBarEntry, NavBarEntryAdmin)
