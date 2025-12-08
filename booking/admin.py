from django.contrib import admin

from .models import Family, Reservation


@admin.register(Family)
class FamilyAdmin(admin.ModelAdmin):
    list_display = ("code", "display_name", "user", "is_free_family")
    search_fields = ("code", "display_name", "user__username")


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = (
        "family",
        "start_date",
        "end_date",
        "is_free",
        "total_price",
        "checked_in_at",
        "checked_out_at",
    )
    list_filter = ("family", "is_free", "start_date")
    search_fields = ("family__display_name", "family__code")