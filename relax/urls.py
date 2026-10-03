from django.urls import path

from . import views

app_name = 'relax'

urlpatterns = [
    path('', views.RelaxHomeView.as_view(), name='home'),
    path('snake/', views.SnakeGameView.as_view(), name='snake'),
    path('racing/', views.RacingGameView.as_view(), name='racing'),
    path('score/', views.SubmitScoreView.as_view(), name='submit_score'),
]
