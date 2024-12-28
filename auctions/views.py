from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from .forms import ListingForm, BidForm, CommentForm
from .models import User, Listing, Watchlist


def index(request):
    list_user = Listing.objects.filter(active=True).order_by("-created")
    paginator = Paginator(list_user, 10)
    page_number = request.GET.get("page")
    page_listings = paginator.get_page(page_number)
    return render(request, "auctions/index.html", {"listings": page_listings})


def login_view(request):
    if request.method == "POST":
        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        return render(
            request,
            "auctions/login.html",
            {"message": "Invalid username and/or password."},
        )
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(
                request, "auctions/register.html", {"message": "Passwords must match."}
            )

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(
                request,
                "auctions/register.html",
                {"message": "Username already taken."},
            )
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")


@login_required
def new_auctions(request):
    category_choices = ListingForm.CATEGORY_CHOICES
    if request.method == "POST":
        form = ListingForm(request.POST)
        if form.is_valid():
            # Set the logged-in user
            listing = form.save(commit=False)  # Don't save yet
            listing.user = request.user  # Set the user
            listing.save()  # Now save the Listing}
            messages.success(request, "Your listing has been created.")
            return redirect("index")
        messages.error(request, "There was an error with created your listing.")
        return render(
            request,
            "auctions/newAuctions.html",
            {"form": form, "category_choices": category_choices},
        )
    else:
        form = ListingForm()
    return render(
        request,
        "auctions/newAuctions.html",
        {"form": form, "category_choices": category_choices},
    )


def listing(request, listing_id):
    auction = get_object_or_404(Listing, id=listing_id)
    comments = auction.comments.all()
    form = CommentForm()
    return render(
        request,
        "auctions/auction.html",
        {"listing": auction, "comments": comments, "form": form},
    )


@login_required
def bid(request, listing_id):
    auction = get_object_or_404(Listing, pk=listing_id)
    comment_auction = auction.comments.all().count()
    if request.method == "POST":
        bid_form = BidForm(request.POST)
        if bid_form.is_valid():
            bid_value = bid_form.cleaned_data["amount"]
            try:
                auction.place_bid(user=request.user, bid_value=bid_value)
                messages.success(request, "Your bid has been placed successfully.")
                messages.info(
                    request,
                    f"({comment_auction}) bid(s) so far. Your bid is the current bid.",
                )
                return redirect("listing", listing_id=listing_id)
            except ValidationError as e:
                bid_form.add_error("amount", str(e)[2:-2])
        else:
            messages.error(
                request,
                "There was an error with your bid. Please review and try again.",
            )
        return render(
            request,
            "auctions/auction.html",
            {"listing": auction, "form": bid_form, "comments": auction.comments.all()},
        )
    return None


def watchlist(request, listing_id):
    user = request.user
    if request.method == "POST":
        listings_in_watchlist = Watchlist.objects.filter(
            user=user, listing__id=listing_id
        )
        if listings_in_watchlist.exists():
            listings_in_watchlist.update(active=True)
            return HttpResponseRedirect(reverse("watchlist", args=[user.id]))
        current_listing = Listing.objects.get(pk=listing_id)
        Watchlist.objects.create(user=user, listing=current_listing, active=True)
        return HttpResponseRedirect(reverse("watchlist", args=[user.id]))
    else:
        listings_in_watchlist = Listing.objects.filter(
            watchlist__user=user, watchlist__active=True
        ).order_by("-created")
        paginator = Paginator(listings_in_watchlist, 10)
        page_number = request.GET.get("page")
        page_listings = paginator.get_page(page_number)
        return render(request, "auctions/watchList.html", {"listings": page_listings})


def watchlist_remove(request, listing_id):
    user = request.user
    current_listing = Listing.objects.get(pk=listing_id)
    watchlist_item = Watchlist.objects.get(user=user, listing=current_listing)
    watchlist_item.active = False
    watchlist_item.save()
    return HttpResponseRedirect(reverse("watchlist", args=[user.id]))


def close_auction(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id)

    if request.user != listing.user:
        messages.error(request, "You are not authorized to close this auction.")
        return redirect("listing", listing_id=listing_id)
    highest_bid = listing.bids.order_by("-amount").first()
    if highest_bid:
        listing.winner = highest_bid.user
    else:
        messages.warning(request, "No bids were placed on this listing.")
    listing.active = False
    listing.save()
    messages.success(request, "The auction has been closed.")
    return redirect("listing", listing_id=listing_id)


def categories(request):
    category = request.GET.get("category")
    if category:
        listings = Listing.objects.filter(category=category, active=True).order_by(
            "-created"
        )
    else:
        listings = Listing.objects.filter(active=True).order_by("-created")
    paginator = Paginator(listings, 10)
    page_number = request.GET.get("page")
    listings = paginator.get_page(page_number)
    return render(
        request,
        "auctions/categories.html",
        {
            "listings": listings,
            "category_choices": ListingForm.CATEGORY_CHOICES,
            "selected_category": category,
        },
    )


@login_required
def comment(request, listing_id):
    auction = get_object_or_404(Listing, pk=listing_id)
    comments = auction.comments.filter(listing=auction)
    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            comment_auction = form.save(commit=False)
            comment_auction.user = request.user
            comment_auction.listing = auction
            comment_auction.save()
            messages.success(request, "Your comment has been added.")
        else:
            messages.error(request, "There was an error with your comment.")
            return render(
                request,
                "auctions/auction.html",
                {"listing": auction, "comments": comments, "form": form},
            )
    return redirect("listing", listing_id=listing_id)
