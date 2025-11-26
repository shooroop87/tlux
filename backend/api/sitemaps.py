# backend/api/sitemaps.py
from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.conf import settings


class MultilingualSitemap(Sitemap):
    """Базовый класс для мультиязычных sitemap"""
    protocol = 'https'
    i18n = True
    alternates = True
    x_default = True


class StaticPagesSitemap(MultilingualSitemap):
    """Статические страницы сайта"""
    changefreq = 'monthly'
    priority = 0.8
    
    def items(self):
        return [
            {'name': 'index', 'priority': 1.0, 'changefreq': 'daily'},
            {'name': 'about', 'priority': 0.8, 'changefreq': 'monthly'},
            {'name': 'contacts', 'priority': 0.7, 'changefreq': 'monthly'},
            {'name': 'help', 'priority': 0.7, 'changefreq': 'weekly'},
            {'name': 'privacy', 'priority': 0.3, 'changefreq': 'yearly'},
            {'name': 'terms', 'priority': 0.3, 'changefreq': 'yearly'},
        ]
    
    def location(self, item):
        return reverse(f"api:{item['name']}")
    
    def priority(self, item):
        return item['priority']
    
    def changefreq(self, item):
        return item['changefreq']
