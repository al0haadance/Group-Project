from django import forms
from .models import SiteSettings


class SiteSettingsForm(forms.ModelForm):
    class Meta:
        model = SiteSettings
        fields = ['site_title', 'background_image', 'background_video', 'overlay_opacity']
        labels = {
            'site_title': 'Назва порталу',
            'background_image': 'Фонове зображення (буде розтягнуте на весь екран)',
            'background_video': 'Фонове відео (mp4) — має пріоритет над зображенням',
            'overlay_opacity': 'Затемнення фону (%), для читабельності тексту',
        }
