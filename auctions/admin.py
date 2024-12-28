from django.contrib import admin

from .models import Listing, Bid, Comment, Watchlist, User


# Register your models here.
@admin.action(description="Make active")
def make_active(modeladmin, request, queryset):
    queryset.update(active=True)


@admin.action(description="Make inactive")
def make_inactive(modeladmin, request, queryset):
    queryset.update(active=False)


class ListingAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "starting_bid",
        "current_bid",
        "category",
        "created",
        "user",
        "active",
        "winner",
    )
    list_filter = ("category", "active")
    search_fields = ["user__username", "title"]
    actions = [make_active, make_inactive]


class BidAdmin(admin.ModelAdmin):
    search_fields = ["user__username", "listing__title"]
    list_display = ["amount", "user", "listing"]
    list_filter = ["listing__title"]


class CommentAdmin(admin.ModelAdmin):
    list_display = ("text", "user", "listing", "listing__title")
    search_fields = ("user__username", "listing__title")


class WatchlistAdmin(admin.ModelAdmin):
    list_display = ("user", "listing", "active")
    list_filter = ("active", "user__username")
    search_fields = ("user__username", "listing__title")
    actions = [make_active, make_inactive]


class UserAdmin(admin.ModelAdmin):
    list_display = ("username", "email", "first_name", "last_name", "date_joined")
    search_fields = ("username", "email")


admin.site.register(Listing, ListingAdmin)
admin.site.register(Bid, BidAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(Watchlist, WatchlistAdmin)
admin.site.register(User, UserAdmin)
