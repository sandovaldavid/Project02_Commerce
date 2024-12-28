from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse


class User(AbstractUser):
    pass


class Listing(models.Model):
    title = models.CharField(max_length=64, blank=True)
    description = models.TextField(blank=True)
    starting_bid = models.DecimalField(max_digits=10, decimal_places=2, blank=True)
    current_bid = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    image = models.URLField(blank=True)
    category = models.CharField(max_length=64, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="listings")
    active = models.BooleanField(default=True)
    winner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="won_listings",
        blank=True,
        null=True,
    )

    def __str__(self):
        return f"{self.title} - {self.starting_bid}"

    def get_remove_url(self, request=None):
        relative_url = reverse("watchlist_remove", args=[self.id])
        if request:
            return request.build_absolute_uri(relative_url)
        return relative_url

    def place_bid(self, user, bid_value):
        if self.current_bid is not None and bid_value <= self.current_bid:
            raise ValidationError("The bid must be higher than the current bid.")
        self.current_bid = bid_value
        self.save()
        Bid.objects.create(user=user, listing=self, amount=bid_value)


class Bid(models.Model):
    amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bids")
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="bids")

    def __str__(self):
        return f"{self.user} bid {self.amount} on {self.listing.title}"


class Comment(models.Model):
    text = models.TextField(blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    listing = models.ForeignKey(
        Listing, on_delete=models.CASCADE, related_name="comments"
    )

    def __str__(self):
        return f"{self.user} commented on {self.listing.title}"


class Watchlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="watchlist")
    listing = models.ForeignKey(
        Listing, on_delete=models.CASCADE, related_name="watchlist"
    )
    active = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user} added {self.listing.title} to watchlist"
