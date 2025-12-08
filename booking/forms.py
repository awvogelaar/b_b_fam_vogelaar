from datetime import date

from django import forms
from django.core.exceptions import ValidationError

from .models import Reservation


class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ["start_date", "end_date"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "end_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
        }
        labels = {
            "start_date": "Startdatum",
            "end_date": "Einddatum",
        }

    def __init__(self, *args, **kwargs):
        self.family = kwargs.pop("family", None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get("start_date")
        end = cleaned_data.get("end_date")

        if not start or not end:
            return cleaned_data

        if start > end:
            raise ValidationError("Startdatum mag niet na einddatum liggen.")

        today = date.today()
        if start < today:
            raise ValidationError("Je kunt niet in het verleden reserveren.")

        nights = (end - start).days + 1
        if nights > 5:
            raise ValidationError("Je kunt maximaal 5 nachten per reservering boeken.")

        # Overlapping check: er mag maar 1 gezin per nacht
        from .models import Reservation

        overlapping = Reservation.objects.filter(
            end_date__gte=start,
            start_date__lte=end,
        )
        if self.instance.pk:
            overlapping = overlapping.exclude(pk=self.instance.pk)

        if overlapping.exists():
            raise ValidationError(
                "Er is al een reservering in (een deel van) deze periode. "
                "Per nacht kan slechts 1 gezin reserveren."
            )

        # Max 5 toekomstige nachten in totaal voor dit gezin
        if self.family:
            future_res = Reservation.objects.filter(
                family=self.family,
                end_date__gte=today,
            )
            total_future_nights = 0
            for r in future_res:
                total_future_nights += (r.end_date - r.start_date).days + 1
            total_future_nights += nights

            if total_future_nights > 5:
                raise ValidationError(
                    "Dit gezin heeft dan meer dan 5 toekomstige nachten openstaan. "
                    "Dat mag niet."
                )

        return cleaned_data