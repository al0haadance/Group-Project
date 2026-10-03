import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.views import View
from django.views.generic import TemplateView

from .models import HighScore


class RelaxHomeView(TemplateView):
    """Вкладка 'Відпочинок' — місце для паузи між навчанням: тут лежать ігри."""
    template_name = 'relax/home.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['top_snake'] = HighScore.objects.select_related('user').filter(game='snake')[:5]
        ctx['top_racing'] = HighScore.objects.select_related('user').filter(game='racing')[:5]
        if self.request.user.is_authenticated:
            ctx['my_snake_best'] = HighScore.objects.filter(user=self.request.user, game='snake').first()
            ctx['my_racing_best'] = HighScore.objects.filter(user=self.request.user, game='racing').first()
        return ctx


class SnakeGameView(TemplateView):
    """Гра 'Змійка' на HTML5 canvas."""
    template_name = 'relax/snake.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['my_best'] = 0
        if self.request.user.is_authenticated:
            record = HighScore.objects.filter(user=self.request.user, game='snake').first()
            ctx['my_best'] = record.best_score if record else 0
        return ctx


class RacingGameView(TemplateView):
    """Гра 'Гонки' — ухилення від машин на трасі, на HTML5 canvas."""
    template_name = 'relax/racing.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['my_best'] = 0
        if self.request.user.is_authenticated:
            record = HighScore.objects.filter(user=self.request.user, game='racing').first()
            ctx['my_best'] = record.best_score if record else 0
        return ctx


class SubmitScoreView(LoginRequiredMixin, View):
    """Приймає новий рахунок від гри (fetch з JS) і оновлює рекорд, якщо він вищий."""

    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body or '{}')
            score = int(data.get('score', 0))
            game = data.get('game', 'snake')
        except (ValueError, TypeError, json.JSONDecodeError):
            return JsonResponse({'ok': False, 'error': 'bad payload'}, status=400)

        if game not in dict(HighScore.GAME_CHOICES):
            return JsonResponse({'ok': False, 'error': 'unknown game'}, status=400)

        score = max(0, min(score, 1_000_000))  # захист від абсурдних значень

        record, _ = HighScore.objects.get_or_create(user=request.user, game=game)
        is_new_best = score > record.best_score
        if is_new_best:
            record.best_score = score
            record.save()

        return JsonResponse({'ok': True, 'best_score': record.best_score, 'is_new_best': is_new_best})
