from django.conf import settings
from django.db import models
from django.utils import timezone
from datetime import date
from decimal import Decimal


class Family(models.Model):
    """
    Familie-eenheid (gezin) die kan reserveren.
    De drie vaste gezinnen zijn gratis.
    Andere families betalen 75 euro per nacht.
    """

    FAMILY_CHOICES = [
        ("adian_julia", "Adian en Julia"),
        ("marten_marilene", "Marten en Marilene"),
        ("quintijn_rosanne", "Quintijn en Rosanne"),
    ]

    code = models.CharField(
        max_length=64,
        unique=True,
        help_text="Bijvoorbeeld 'adian_julia' of een andere familienaam.",
    )
    display_name = models.CharField(
        max_length=128,
        blank=True,
        help_text="Naam die op de site wordt getoond. Leeg = gebruik code/keuze.",
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="family",
        help_text="Account dat namens dit gezin kan reserveren.",
    )

    is_free_family = models.BooleanField(
        default=False,
        help_text="Als dit aan staat, zijn reserveringen gratis.",
    )

    def __str__(self):
        if self.display_name:
            return self.display_name
        # als code in de drie bekende choices zit, gebruik daar de label van
        choices_dict = dict(self.FAMILY_CHOICES)
        return choices_dict.get(self.code, self.code)


class Reservation(models.Model):
    """
    Reservering van 1 gezin voor 1 of meer nachten.
    Regels:
    - Per nacht maar 1 gezin (globaal)
    - Maximaal 5 nachten toekomst per gezin tegelijk
    - Drie specifieke gezinnen gratis, andere families betalen 75 euro/ nacht
    """

    family = models.ForeignKey(
        Family,
        on_delete=models.CASCADE,
        related_name="reservations",
        verbose_name="Gein",
    )
    start_date = models.DateField("Startdatum")
    end_date = models.DateField(
        "Einddatum",
        help_text="Laatste overnachtingsdatum (check-out is de volgende ochtend).",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    price_per_night = models.DecimalField(
        max_digits=7, decimal_places=2, default=Decimal("75.00")
    )
    total_price = models.DecimalField(
        max_digits=9, decimal_places=2, default=Decimal("0.00")
    )
    is_free = models.BooleanField(default=False)

    checked_in_at = models.DateTimeField(null=True, blank=True)
    checked_out_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-start_date"]

    def __str__(self):
        return f"{self.family} van {self.start_date} t/m {self.end_date}"

    @property
    def number_of_nights(self):
        return (self.end_date - self.start_date).days + 1

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.start_date > self.end_date:
            raise ValidationError("Startdatum mag niet na einddatum liggen.")

    def save(self, *args, **kwargs):
        # prijslogica
        if self.family.is_free_family:
            self.is_free = True
            self.total_price = Decimal("0.00")
        else:
            nights = self.number_of_nights
            self.is_free = False
            self.total_price = self.price_per_night * nights
        super().save(*args, **kwargs)

    def overlaps_with(self, start, end):
        """
        Checkt of deze reservering overlapt met een gegeven periode.
        """
        return not (self.end_date < start or self.start_date > end)

    @property
    def can_check_in(self):
        today = date.today()
        return (
            self.checked_in_at is None
            and self.start_date <= today <= self.end_date
        )

    @property
    def can_check_out(self):
        return self.checked_in_at is not None and self.checked_out_at is None

    def do_check_in(self):
        if self.can_check_in:
            self.checked_in_at = timezone.now()
            self.save()

    def do_check_out(self):
        if self.can_check_out:
            self.checked_out_at = timezone.now()
            self.save()