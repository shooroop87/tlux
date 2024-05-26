from api import views
from django.urls import path

app_name = 'api'


urlpatterns = [
    path('booking-vehicle/', views.vehicle, name='vehicle'),
    path('booking-extra/', views.extras, name='extras'),
    path('booking-passenger/', views.details, name='details'),
    path('booking-payment/', views.payment, name='payment'),
    path('pay/', views.nexi, name='nexi'),
    path('about/', views.about, name='about'),
    path('contacts/', views.contacts, name='contacts'),
    path('privacy-policy/', views.privacy, name='privacy'),
    path('terms-and-conditions/', views.terms, name='terms'),
    path('help-center/', views.help, name='help'),
    path('emailtest', views.emailtest, name='emailtest'),
    path('', views.index, name='index')
]
