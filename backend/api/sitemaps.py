from django.contrib.sitemaps import Sitemap
from django.shortcuts import reverse


class StaticViewSitemap(Sitemap):
    def items(self):
        return ['about', 'index']

    def location(self, item):
        return reverse(f"api:{item}")
