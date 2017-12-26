import datetime
from django.contrib import admin
from django.utils.html import escape
from django.core import urlresolvers
from django.contrib import messages
from daterange_filter.filter import DateRangeFilter
from django.contrib.admin.models import LogEntry, DELETION

from .models import Location, Device, Person, Booking


# =======================================================================================
# LOCATION
# =======================================================================================
class LocationAdmin(admin.ModelAdmin):
    list_display = ('location_name',)


# =======================================================================================
# PERSON
# =======================================================================================
class PersonAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Account',     {'fields': ['username',]}),
        ('Details',     {'fields': ['first_name', 'last_name', 'email', 'office', 'role']}),
        ('Permissions', {'fields': ['groups',]}),
        ('Activation',  {'fields': ['is_staff', 'is_active', 'last_login', 'date_joined']}),
    ]
    list_display = ('full_name', 'office', 'role')
    list_filter = ('office__location_name', 'role')
    search_fields = ('first_name', 'last_name')


# =======================================================================================
# DEVICE
# =======================================================================================
def export_csv(modeladmin, request, queryset):
    import csv
    from django.http import HttpResponse
    from django.utils.encoding import smart_str
    response = HttpResponse()
    response['Content-Disposition'] = 'attachment; filename=assets.csv'
    writer = csv.writer(response, csv.excel)
    response.write(u'\ufeff'.encode('utf8'))
    writer.writerow([
        smart_str(u"Brand"),
        smart_str(u"Model"),
        smart_str(u"OS Name"),
        smart_str(u"OS Version"),
        smart_str(u"Serial"),
        smart_str(u"Rooted"),
    ])
    for obj in queryset:
        writer.writerow([
            smart_str(obj.brand),
            smart_str(obj.model),
            smart_str(obj.os_name),
            smart_str(obj.os_version),
            smart_str(obj.serial_num),
            smart_str(obj.rooted)
        ])
    return response
export_csv.short_description = u"Export CSV"



class DeviceAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Hardware',  {'fields': ['brand', 'model']}),
        ('Software',  {'fields': ['os_name', 'os_version']}),
        ('Asset',     {'fields': ['serial_num', 'asset_num', 'office']}),
        ('Various',   {'fields': ['rooted', 'passcode', 'notes']}),
    ]
    readonly_fields = ('free',)
    list_display = ('hardware_info', 'software_info', 'serial_num', 'asset_num', 'office', 'rooted', 'passcode', 'notes', 'free', 'used_by', 'bookings')
    list_filter = ('office', 'rooted', 'os_name', 'model')
    search_fields = ('model', 'os_name', 'os_version', 'serial_num', 'asset_num')
    actions = [export_csv]

    def free(self, obj):
        not_returned = Booking.objects.filter(device=obj,returned=False)
        is_free = False if not_returned else True
        return is_free
    free.boolean = True

    def used_by(self, obj):
        if self.free(obj):
            user = ''
        else:
            bookings = Booking.objects.filter(device=obj,returned=False).order_by('-date_to')
            if bookings:
                user = bookings[0].person
            else:
                user = ''
        return user

    def bookings(self, obj):
        url = urlresolvers.reverse('admin:assets_booking_changelist')
        return '<a href="{0}?device__asset_num={1}">See List</a>'.format(url, obj.asset_num)
    bookings.allow_tags = True


# =======================================================================================
# BOOKING
# =======================================================================================
class BookingAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Consultant & Device',     {'fields': [('person', 'device')]}),
        ('Dates',     {'fields': [('date_from', 'date_to')]}),
        ('Other',     {'fields': ['returned', 'notes']}),
    ]
    readonly_fields = ('edit', 'overdue')
    list_display = ('edit', 'person', 'booked_device', 'date_from', 'date_to', 'returned', 'overdue', 'notes')
    list_filter = ('device__os_name', 'device__office', 'returned',
                   ('date_from', DateRangeFilter),
                   ('date_to', DateRangeFilter),)
    search_fields = ('person__last_name', 'device__asset_num', 'device__serial_num')
    list_display_links = ('edit',)

    def edit(self, obj):
        return "Edit Booking"

    def booked_device(self, obj):
        link = urlresolvers.reverse("admin:assets_device_change", args=[obj.device.asset_num])
        return u'<a href="%s">%s</a>' % (link, obj.device)
    booked_device.allow_tags = True

    def overdue(self, obj):
        today = datetime.date.today()
        bookings = Booking.objects.filter(device=obj.device)
        not_returned = filter(lambda x: x.returned is False, bookings)
        actual_not_returned = filter(lambda x: today >= x.date_to, not_returned)
        return True if actual_not_returned else False
    overdue.boolean = True


    def save_model(self, request, obj, form, change):
        # Retrieve users
        obj.user = request.user
        user_session = obj.user
        user_booking = obj.person.username
        # Retrieve user's groups
        groups = user_session.groups.all()
        consult = filter(lambda x: "CONSULTANTS" in x.name, groups)
        if consult:
            # If consultant, check if he is adding himself
            if str(user_session) != str(user_booking):
                messages.add_message(request, messages.ERROR, 'ERROR: You cannot assign a booking to another consultant. '
                                                              'The modification has not been saved')
                return
            # If consultant, check he is not trying to return a device
            if obj.returned:
                messages.add_message(request, messages.ERROR, 'ERROR: Only ECs are allowed to mark a device as Returned.')
                return
        obj.save()



# =======================================================================================
# LOG ENTRIES
# =======================================================================================
class LogEntryAdmin(admin.ModelAdmin):
    date_hierarchy = 'action_time'
    readonly_fields = [f.name for f in LogEntry._meta.get_fields()]
    list_filter = [
        'user',
        'content_type',
        'action_flag'
    ]
    search_fields = [
        'object_repr',
        'change_message'
    ]
    list_display = [
        'action_time',
        'user',
        'content_type',
        'object_link',
        'action_flag',
        'change_message',
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser and request.method != 'POST'

    def has_delete_permission(self, request, obj=None):
        return False

    def object_link(self, obj):
        if obj.action_flag == DELETION:
            link = escape(obj.object_repr)
        else:
            ct = obj.content_type
            link = u'<a href="%s">%s</a>' % (
                urlresolvers.reverse('admin:%s_%s_change' % (ct.app_label, ct.model), args=[obj.object_id]),
                escape(obj.object_repr),
            )
        return link
    object_link.allow_tags = True
    object_link.admin_order_field = 'object_repr'
    object_link.short_description = u'object'

    def queryset(self, request):
        return super(LogEntryAdmin, self).queryset(request) \
            .prefetch_related('content_type')


# =======================================================================================
# REGISTER MODELS
# =======================================================================================
admin.site.register(Location, LocationAdmin)
admin.site.register(Person, PersonAdmin)
admin.site.register(Device, DeviceAdmin)
admin.site.register(Booking, BookingAdmin)
admin.site.register(LogEntry, LogEntryAdmin)
