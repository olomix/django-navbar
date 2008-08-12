from django.contrib import admin
from models import NavBarEntry

class NavBarEntryAdmin(admin.ModelAdmin):
    """
    Defines admin display and functionality for NavBarEntry.

    """

    fieldsets = (
        (None, {'fields': ('name', 'title', 'url', 'order', 'parent')}),
        ('Advanced Permissions', {'classes': 'collapse',
                         'fields': ('user_type', 'groups', )}),
    )
    list_filter = ('parent',)
    list_display = ('name', 'url', 'order', 'parent')
    search_fields = ('url', 'name', 'title')

admin.site.register(NavBarEntry, NavBarEntryAdmin)

