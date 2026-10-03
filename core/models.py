import colorsys

from django.db import models

# Кольори теми "Glass Night" за замовчуванням (використовуються, коли фон не завантажений
# або коли з фото не вдалося виділити виразні кольори).
DEFAULT_THEME = {
    'theme_bg': '#0f1117',
    'theme_bg_2': '#171a24',
    'theme_accent': '#ff8a4c',
    'theme_accent_2': '#6ea8fe',
}


class SiteSettings(models.Model):
    """
    Налаштування порталу (singleton — завжди один запис).
    Дозволяє змінювати фонове зображення сайту без правок коду.
    """
    site_title = models.CharField(max_length=100, default='Портал групи', verbose_name='Назва порталу')
    background_image = models.ImageField(
        upload_to='site/', blank=True, null=True, verbose_name='Фонове зображення'
    )
    background_video = models.FileField(
        upload_to='site/video/', blank=True, null=True, verbose_name='Фонове відео',
        help_text='Якщо завантажено — відео показується замість фото (mp4, без звуку, в циклі).'
    )
    overlay_opacity = models.PositiveIntegerField(
        default=55,
        verbose_name='Затемнення фону (%)',
        help_text='0 — фон без затемнення, 100 — повністю чорний. Впливає на читабельність тексту.'
    )

    # Кольори теми, автоматично виділені з background_image. Зберігаються в БД,
    # щоб не перераховувати палітру на кожен рендер сторінки.
    theme_bg = models.CharField(max_length=7, default=DEFAULT_THEME['theme_bg'])
    theme_bg_2 = models.CharField(max_length=7, default=DEFAULT_THEME['theme_bg_2'])
    theme_accent = models.CharField(max_length=7, default=DEFAULT_THEME['theme_accent'])
    theme_accent_2 = models.CharField(max_length=7, default=DEFAULT_THEME['theme_accent_2'])

    class Meta:
        verbose_name = 'Налаштування сайту'
        verbose_name_plural = 'Налаштування сайту'

    def __str__(self):
        return self.site_title

    def save(self, *args, **kwargs):
        self.pk = 1  # завжди один запис (singleton)
        super().save(*args, **kwargs)
        if self.background_image:
            self._update_theme_from_image()

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def _update_theme_from_image(self):
        """
        Аналізує завантажене фонове зображення та підбирає під нього кольори теми:
        темний відтінок фону (з тим самим тоном, що й фото) + два акцентні кольори
        (найбільш насичені кольори з палітри фото). Оновлює запис у БД напряму
        через .update(), щоб не викликати save() повторно.
        """
        try:
            from PIL import Image
        except ImportError:
            return

        try:
            with Image.open(self.background_image.path) as img:
                img = img.convert('RGB')
                img.thumbnail((150, 150))
                pixels = list(img.getdata())
        except (FileNotFoundError, OSError):
            return

        if not pixels:
            return

        # Рахуємо середній колір (для фону) і шукаємо найбільш насичені кольори (для акцентів).
        total = len(pixels)
        avg_r = sum(p[0] for p in pixels) / total
        avg_g = sum(p[1] for p in pixels) / total
        avg_b = sum(p[2] for p in pixels) / total
        avg_h, avg_l, avg_s = colorsys.rgb_to_hls(avg_r / 255, avg_g / 255, avg_b / 255)

        # Темний фон у тоні фото: беремо відтінок середнього кольору, але
        # притлумлюємо яскравість і насиченість, щоб текст залишався читабельним.
        bg_hex = self._hls_to_hex(avg_h, 0.08, min(avg_s * 0.7, 0.35))
        bg2_hex = self._hls_to_hex(avg_h, 0.12, min(avg_s * 0.7, 0.35))

        # Кандидати на акцентні кольори: унікальні кольори палітри, відсортовані
        # за насиченістю та "виразністю" (не надто темні й не надто світлі).
        seen = {}
        for r, g, b in pixels:
            key = (r // 16, g // 16, b // 16)  # групуємо близькі кольори
            seen[key] = seen.get(key, 0) + 1

        candidates = []
        for (rk, gk, bk), count in seen.items():
            r, g, b = rk * 16 + 8, gk * 16 + 8, bk * 16 + 8
            h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
            if 0.15 <= l <= 0.85 and s >= 0.25:
                candidates.append((count, h, l, s))
        candidates.sort(key=lambda c: (c[3], c[0]), reverse=True)

        accent_hex = DEFAULT_THEME['theme_accent']
        accent2_hex = DEFAULT_THEME['theme_accent_2']

        if candidates:
            h0 = candidates[0][1]
            # Робимо акцент яскравим і читабельним незалежно від вихідної яскравості фото.
            accent_hex = self._hls_to_hex(h0, 0.62, max(candidates[0][3], 0.55))

            # Другий акцент шукаємо серед кольорів з достатньо іншим відтінком (hue).
            second = next(
                (c for c in candidates[1:] if min(abs(c[1] - h0), 1 - abs(c[1] - h0)) > 0.12),
                None
            )
            if second:
                accent2_hex = self._hls_to_hex(second[1], 0.68, max(second[3], 0.45))
            else:
                # Якщо другого чіткого кольору немає — зсуваємо відтінок першого.
                accent2_hex = self._hls_to_hex((h0 + 0.5) % 1.0, 0.68, max(candidates[0][3], 0.45))

        SiteSettings.objects.filter(pk=1).update(
            theme_bg=bg_hex,
            theme_bg_2=bg2_hex,
            theme_accent=accent_hex,
            theme_accent_2=accent2_hex,
        )
        self.theme_bg, self.theme_bg_2 = bg_hex, bg2_hex
        self.theme_accent, self.theme_accent_2 = accent_hex, accent2_hex

    @staticmethod
    def _hls_to_hex(h, l, s):
        r, g, b = colorsys.hls_to_rgb(h, l, s)
        return '#{:02x}{:02x}{:02x}'.format(round(r * 255), round(g * 255), round(b * 255))
