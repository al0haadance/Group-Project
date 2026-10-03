from django.contrib import admin

from .models import HighScore


@admin.register(HighScore)
class HighScoreAdmin(admin.ModelAdmin):
    list_display = ('user', 'best_score', 'updated_at')
    ordering = ('-best_score',)
