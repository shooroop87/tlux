# backend/api/sitemaps.py
from django.conf import settings
from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import override as translation_override


class CompleteSitemap(Sitemap):
    """Мультиязычный sitemap для TransfersLux"""

    protocol = "https"

    def __init__(self):
        self.languages = [lang[0] for lang in settings.LANGUAGES]

    def items(self):
        """Возвращает кортежи (url_name, language_code)"""
        items = []
        url_names = [
            "index",
            "about",
            "contacts",
            "help",
            "privacy",
            "terms",
        ]

        for url_name in url_names:
            for lang_code in self.languages:
                items.append((url_name, lang_code))

        return items

    def location(self, item):
        url_name, lang_code = item

        with translation_override(lang_code):
            try:
                url = reverse(f"api:{url_name}")

                # Для языка по умолчанию URL без префикса
                if lang_code == settings.LANGUAGE_CODE:
                    return url
                else:
                    # Для других языков добавляем префикс
                    if not url.startswith(f"/{lang_code}/"):
                        url = f"/{lang_code}{url}"
                    return url

            except Exception as e:
                print(f"Ошибка генерации URL для {url_name} на языке {lang_code}: {e}")
                return None

    def lastmod(self, item):
        return timezone.now()

    def priority(self, item):
        url_name, lang_code = item

        priorities = {
            "index": 1.0,
            "about": 0.8,
            "contacts": 0.7,
            "help": 0.7,
            "privacy": 0.3,
            "terms": 0.3,
        }
        return priorities.get(url_name, 0.5)

    def changefreq(self, item):
        url_name, lang_code = item

        changefreqs = {
            "index": "daily",
            "about": "monthly",
            "contacts": "monthly",
            "help": "weekly",
            "privacy": "yearly",
            "terms": "yearly",
        }
        return changefreqs.get(url_name, "monthly")