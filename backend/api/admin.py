from api.models import Booking, Search
from django.contrib import admin


class SearchAdmin(admin.ModelAdmin):
    list_display = [f.name for f in Search._meta.get_fields()]
    empty_value_display = '-empty-'


class BookingAdmin(admin.ModelAdmin):
    list_display = [f.name for f in Booking._meta.get_fields()]
    empty_value_display = '-empty-'


admin.site.register(Search, SearchAdmin)
admin.site.register(Booking, BookingAdmin)
