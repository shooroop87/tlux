# context_processors.py
from django.conf import settings

def google_maps_api_key(request):
    print(f"Google Maps API Key: {settings.GOOGLE_MAPS_API_KEY}")  # Для отладки
    return {'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY}
