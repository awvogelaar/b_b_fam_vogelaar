from django.urls import path

from . import views

app_name = "booking"

urlpatterns = [
    path("", views.home, name="home"),
    path("reservations/", views.reservation_list, name="reservation_list"),
    path("reservations/new/", views.reservation_create, name="reservation_create"),
    path("reservations/<int:pk>/", views.reservation_detail, name="reservation_detail"),
    path(
        "reservations/<int:pk>/checkin/",
        views.reservation_checkin,
        name="reservation_checkin",
    ),
    path(
        "reservations/<int:pk>/checkout/",
        views.reservation_checkout,
        name="reservation_checkout",
    ),
    path("availability/", views.availability_view, name="availability"),
]