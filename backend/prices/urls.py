from django.urls import path

from .views import game_price


urlpatterns = [path("games/<slug:slug>/", game_price, name="game-price-v1")]
