from django.conf import settings
from django.db import models


class HighScore(models.Model):
    """Найкращий рахунок гравця в одній з ігор розділу 'Відпочинок'."""
    GAME_CHOICES = (
        ('snake', 'Змійка'),
        ('racing', 'Гонки'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='game_scores')
    game = models.CharField(max_length=10, choices=GAME_CHOICES, default='snake')
    best_score = models.PositiveIntegerField(default=0, verbose_name='Найкращий рахунок')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-best_score']
        unique_together = ('user', 'game')
        verbose_name = 'Рекорд'
        verbose_name_plural = 'Рекорди'

    def __str__(self):
        return f'{self.user.username} / {self.get_game_display()}: {self.best_score}'
