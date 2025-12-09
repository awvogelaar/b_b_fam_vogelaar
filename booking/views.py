from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .forms import ReservationForm
from .models import Reservation, Family


def get_family_for_user(user):
    """
    Haal het Family-object op dat aan de ingelogde gebruiker gekoppeld is.
    """
    if not user.is_authenticated:
        return None
    try:
        return user.family
    except Family.DoesNotExist:
        return None


def home(request):
    """
    Eenvoudige homepage.
    """
    family = get_family_for_user(request.user)
    context = {
        "family": family,
        "today": date.today(),
    }
    return render(request, "booking/home.html", context)


@login_required
def reservation_list(request):
    family = get_family_for_user(request.user)
    if family:
        reservations = Reservation.objects.filter(family=family)
    else:
        # user zonder gekoppeld gezin: toon alles (kan handig zijn voor beheer)
        reservations = Reservation.objects.all().select_related("family")

    return render(
        request,
        "booking/reservation_list.html",
        {"reservations": reservations, "family": family},
    )


@login_required
def reservation_create(request):
    family = get_family_for_user(request.user)
    if not family:
        messages.error(
            request, "Je account is nog niet gekoppeld aan een gezin."
        )
        return redirect("booking:home")

    if request.method == "POST":
        form = ReservationForm(request.POST, family=family)
        if form.is_valid():
            reservation = form.save(commit=False)
            reservation.family = family
            reservation.save()
            messages.success(request, "Reservering is aangemaakt.")
            return redirect("booking:reservation_detail", pk=reservation.pk)
    else:
        form = ReservationForm(family=family)

    return render(
        request,
        "booking/reservation_create.html",
        {"form": form, "family": family},
    )


@login_required
def reservation_detail(request, pk):
    reservation = get_object_or_404(Reservation, pk=pk)
    family = get_family_for_user(request.user)
    if family and reservation.family != family and not request.user.is_staff:
        messages.error(request, "Je mag alleen je eigen reserveringen bekijken.")
        return redirect("booking:reservation_list")

    return render(
        request,
        "booking/reservation_detail.html",
        {
            "reservation": reservation,
            "family": family,
        },
    )


@login_required
@require_POST
def reservation_checkin(request, pk):
    reservation = get_object_or_404(Reservation, pk=pk)
    family = get_family_for_user(request.user)

    if not family or reservation.family != family:
        if not request.user.is_staff:
            messages.error(request, "Je mag alleen je eigen reserveringen inchecken.")
            return redirect("booking:reservation_list")

    if reservation.can_check_in:
        reservation.do_check_in()
        messages.success(request, "Je bent succesvol ingecheckt.")
    else:
        messages.error(
            request,
            "Inchecken is nu niet mogelijk. Controleer de datum of eerdere check-in.",
        )

    return redirect("booking:reservation_detail", pk=pk)


@login_required
@require_POST
def reservation_checkout(request, pk):
    reservation = get_object_or_404(Reservation, pk=pk)
    family = get_family_for_user(request.user)

    if not family or reservation.family != family:
        if not request.user.is_staff:
            messages.error(request, "Je mag alleen je eigen reserveringen uitchecken.")
            return redirect("booking:reservation_list")

    if reservation.can_check_out:
        reservation.do_check_out()
        messages.success(request, "Je bent succesvol uitgecheckt.")
    else:
        messages.error(
            request,
            "Uitchecken is nu niet mogelijk. Controleer eerdere check-in/out.",
        )

    return redirect("booking:reservation_detail", pk=pk)


@login_required
def availability_view(request):
    """
    Laat voor iedereen die is ingelogd zien welke data al geboekt zijn
    en welke nog vrij zijn, binnen een bepaalde periode (bijvoorbeeld komende 60 dagen).
    """
    today = date.today()
    horizon = today + timedelta(days=60)  # toon bv. komende 60 dagen

    # Haal alle reserveringen op die overlappen met vandaag–horizon
    reservations = Reservation.objects.filter(
        end_date__gte=today,
        start_date__lte=horizon,
    ).select_related("family")

    # Bouw een set met alle bezette data
    booked_dates = set()
    for r in reservations:
        current = r.start_date
        while current <= r.end_date:
            booked_dates.add(current)
            current = current + timedelta(days=1)

    # Bouw een lijst van dagen in de periode met flag 'is_booked'
    days = []
    current = today
    while current <= horizon:
        days.append(
            {
                "date": current,
                "is_booked": current in booked_dates,
            }
        )
        current = current + timedelta(days=1)

    context = {
        "days": days,
        "today": today,
        "horizon": horizon,
    }
    return render(request, "booking/availability.html", context)