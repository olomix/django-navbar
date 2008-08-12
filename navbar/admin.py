from django.contrib import admin

from navbar.models import NavBarEntry

class NavBarEntryAdmin(admin.ModelAdmin):
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
