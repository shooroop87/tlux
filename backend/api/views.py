import hashlib
import json
import math
import re
import sys
import uuid
from datetime import datetime
from urllib.parse import urljoin

if sys.version_info >= (3,):
    from urllib.parse import urlencode
else:
    from urllib import urlencode

import googlemaps
from api.forms import DetailsForm, ExtrasForm, SearchForm, VehicleForm
from api.models import Booking, Search
from django.conf import settings
from django.contrib import messages
from django.core.mail import EmailMultiAlternatives
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.utils.translation import get_language_from_request

google_api_key = settings.GOOGLE_MAPS_API_KEY


def index(request):
    if request.method == 'POST':
        form = SearchForm(request.POST)
        if form.is_valid():
            from_short = form.cleaned_data["from_short"]
            from_hidden = form.cleaned_data["from_hidden"]
            to_short = form.cleaned_data["to_short"]
            to_hidden = form.cleaned_data["to_hidden"]
            to_date = form.cleaned_data["to_date"]
            to_time = form.cleaned_data["to_time"]
            # Сообщение о заполнении полей
            language_code = get_language_from_request(request)
            errors = {
                'it': 'Si prega di compilare tutti i campi obbligatori',
                'fr': 'Veuillez remplir tous les champs requis',
                'es': 'Por favor, rellene todos los campos obligatorios',
                'ru': 'Пожалуйста, заполните все обязательные поля'}
            error_message = errors[language_code]
            if error_message is None:
                error_message = 'Please fill in all required fields'
            # Если поля не заполнено, вернуть ошибку
            if not all([from_short, to_short, to_date, to_time]):
                messages.error(request, error_message)
            else:
                session_id = uuid.uuid4()
                query = {
                    'from_short': from_short,
                    'from_hidden': from_hidden,
                    'to_short': to_short,
                    'to_hidden': to_hidden,
                    'to_date': to_date,
                    'to_time': to_time,
                    'session_id': str(session_id),
                }
                request.session['search_query'] = query
                return redirect('api:vehicle')
    else:
        form = SearchForm()
    return render(request, 'index.html', {'form': form})


def vehicle(request):
    if 'search_query' in request.session:
        query = request.session['search_query']
        # Access individual fields from the dictionary
        from_short = query.get('from_short')
        from_hidden = query.get('from_hidden')
        to_short = query.get('to_short')
        to_hidden = query.get('to_hidden')
        to_date = query.get('to_date')
        to_time = query.get('to_time')
        session_id = query.get('session_id')
        # Perform your search logic here based on the query
        gmaps = googlemaps.Client(key=google_api_key)
        now = datetime.now()
        calculate = json.dumps(gmaps.distance_matrix(from_hidden,
                                                     to_hidden,
                                                     mode="driving",
                                                     departure_time=now))
        calculate2 = json.loads(calculate)
        distance = calculate2['rows'][0]['elements'][0]['distance']['value']
        # km
        distance_km = round(distance / 1000, 1)
        cost = math.ceil((distance / 1000) * 2)

        directions_result = gmaps.directions(from_hidden,
                                             to_hidden,
                                             mode='driving')

        # Extract travel time from the directions result
        if directions_result:
            route = directions_result[0]['legs'][0]
            travel_time = route['duration']['text']
            # travel_time_h = math.floor(travel_time_value/3600)
            # print(travel_time_h)
            # travel_time_min = re.findall('\d+', travel_time)[0]

        milan_bergamo_rule = ['Milan',
                              'milan',
                              'milano',
                              'Milano',
                              'Malpensa',
                              'malpensa',
                              'Airport',
                              'airport',
                              'bergamo',
                              'Bergamo',
                              'Orio al Serio BG',
                              'Orio al Serio',
                              'BGY',
                              'Aeroporto',
                              'MXP',
                              'aeruporto',
                              'аэропорт',
                              'Аэропорт',
                              'Мальпенса',
                              'Миланский аэропорт',
                              '21010 Ферно, Варезе, Италия']
        checked_from = any(
            re.search(item,
                      from_hidden,
                      re.IGNORECASE) for item in milan_bergamo_rule)
        checked_to = any(
            re.search(item,
                      to_hidden,
                      re.IGNORECASE) for item in milan_bergamo_rule)
        checked = checked_from and checked_to
        if checked:
            cost = 100
        cost_e = max(50, cost)
        cost_s = cost_e * 1.5
        cost_v = cost_e * 1.2
        context = {
            'from_short': from_short,
            'from_hidden': from_hidden,
            'to_short': to_short,
            'to_hidden': to_hidden,
            'cost_e': cost_e,
            'cost_s': cost_s,
            'cost_v': cost_v,
            'distance': distance_km,
            'travel_time': travel_time,
            'to_date': to_date,
            'to_time': to_time,
        }
        # Update query
        query.update({'distance': distance_km, 'travel_time': travel_time})
        request.session['search_query'] = query
        # Save search
        instance = Search(
            from_hidden=from_hidden,
            to_hidden=to_hidden,
            from_short=from_short,
            to_short=to_short,
            to_date=to_date,
            to_time=to_time,
            distance=distance_km,
            travel_time=travel_time,
            session_id=session_id
        )
        instance.save()
        # Save query to pass next page
        request.session['search_query'] = query
        # Render next page
        return render(request, 'booking/booking-vehicle.html', context)
    else:
        return redirect('api:index')


def extras(request):
    if request.method == 'POST':
        form = VehicleForm(request.POST)
        if form.is_valid():
            car_class = form.cleaned_data["car_class"]
            rate = form.cleaned_data["rate"]
            # Retrieve query from session
            query = request.session.get('search_query', {})
            context = {
                'from_short': query['from_short'],
                'from_hidden': query['from_hidden'],
                'to_short': query['to_short'],
                'to_hidden': query['to_hidden'],
                'distance': query['distance'],
                'travel_time': query['travel_time'],
                'to_date': query['to_date'],
                'to_time': query['to_time'],
                'car_class': car_class,
                'rate': rate
            }
            # Update query
            query.update({
                'car_class': car_class,
                'rate': rate,
            })
            request.session['search_query'] = query
            return render(request, 'booking/booking-extra.html', context)
    else:
        form = VehicleForm()
    return render(request, 'booking/booking-vehicle.html', {'form': form})


def details(request):
    if request.method == 'POST':
        form = ExtrasForm(request.POST)
        # breakpoint()
        # print(form)
        if form.is_valid():
            flight = form.cleaned_data["flight"]
            child_seat = form.cleaned_data["child_seat"]
            booster_seat = form.cleaned_data["booster_seat"]
            flowers = form.cleaned_data["flowers"]
            notes_extra = form.cleaned_data["notes_extra"]

            # Query
            query = request.session.get('search_query', {})

            # Calculate costs
            cst = int(child_seat) * 15
            bst = int(booster_seat) * 20
            fl = int(flowers) * 70
            extra_total = int(cst) + int(bst) + int(fl)

            # Convert rate and calculate total
            rate = query.get('rate')
            rate = str(rate).replace(',', '.')
            total = float(rate) + float(extra_total)

            # Update query dictionary
            query.update({
                'total': total,
                'child_seat_total': cst,
                'booster_seat_total': bst,
                'flowers_total': fl,
                'extra_total': extra_total,
                'flight': flight,
                'child_seat': child_seat,
                'booster_seat': booster_seat,
                'flowers': flowers,
                'notes_extra': notes_extra,
            })

            # Store updated query in session
            request.session['search_query'] = query

            # Prepare context
            context = {
                'from_short': query.get('from_short'),
                'from_hidden': query.get('from_hidden'),
                'to_short': query.get('to_short'),
                'to_hidden': query.get('to_hidden'),
                'car_class': query.get('car_class'),
                'rate': query.get('rate'),
                'total': total,
                'child_seat_total': cst,
                'booster_seat_total': bst,
                'flowers_total': fl,
                'extra_total': extra_total,
                'distance': query.get('distance'),
                'travel_time': query.get('travel_time'),
                'to_date': query.get('to_date'),
                'to_time': query.get('to_time'),
                'flight': flight,
                'child_seat': child_seat,
                'booster_seat': booster_seat,
                'flowers': flowers,
                'notes_extra': notes_extra,
            }
            return render(request, 'booking/booking-passenger.html', context)

    # If not POST, prepare context from session query
    query = request.session.get('search_query', {})
    context = {
        'from_short': query.get('from_short'),
        'from_hidden': query.get('from_hidden'),
        'to_short': query.get('to_short'),
        'to_hidden': query.get('to_hidden'),
        'car_class': query.get('car_class'),
        'rate': query.get('rate'),
        'distance': query.get('distance'),
        'travel_time': query.get('travel_time'),
        'to_date': query.get('to_date'),
        'to_time': query.get('to_time'),
    }
    return render(request, 'booking/booking-passenger.html', context)


def payment(request):
    if request.method == 'POST':
        form = DetailsForm(request.POST)
        if form.is_valid():
            # Extract form data
            cleaned_data = form.cleaned_data
            name = cleaned_data["name"]
            lastname = cleaned_data["lastname"]
            email = cleaned_data["email"]
            phone = cleaned_data["phone"]
            passengers = cleaned_data["passengers"]
            luggage = cleaned_data["luggage"]
            notes_details = cleaned_data["notes_details"]

            # Retrieve session data
            query = request.session.get('search_query', {})
            total = query.get('total')

            # Payment gateway settings
            ALIAS_TEST = 'payment_3780564'
            total = str(total).replace(',', '.')
            importo = float(total)
            divisa = 'EUR'
            codTrans = query.get('codTrans')
            requestUrl = query.get('requestUrl')
            success_url = query.get('success_url')
            cancel_url = query.get('cancel_url')
            mac = query.get('mac')

            # Update session query
            query.update({
                'name': name,
                'lastname': lastname,
                'email': email,
                'phone': phone,
                'passengers': passengers,
                'luggage': luggage,
                'notes_details': notes_details,
                'total': total,
                'alias': ALIAS_TEST,
                'importo': importo,
                'divisa': divisa,
                'requestUrl': requestUrl,
                'codTrans': codTrans,
                'url': success_url,
                'url_back': cancel_url,
                'mac': mac,
            })
            request.session['search_query'] = query

    # If not post show page
    # Fields from request
    name = request.POST.get("name")
    lastname = request.POST.get("lastname")

    # Retrieve session data
    query = request.session.get('search_query', {})

    # Calculate additional charges
    child_seat = int(query.get('child_seat', 0))
    booster_seat = int(query.get('booster_seat', 0))
    flowers = int(query.get('flowers', 0))
    cst = child_seat * 15
    bst = booster_seat * 20
    fl = flowers * 70
    extra_total = cst + bst + fl

    # Calculate total cost
    rate = float(str(query.get('rate', '0')).replace(',', '.'))
    total = rate + extra_total

    # Payment gateway settings
    # PROD
    # ALIAS_TEST = 'payment_3780564'
    # CHIAVESEGRETA_TEST = '9086Wh56532BG7oV6giEUW2510201H68WAqc831G'
    # TEST
    ALIAS_TEST = 'ALIAS_WEB_00082258'
    CHIAVESEGRETA_TEST = 'Y665ESJRJEK38D6D1MJJGCYAUQR2J8SV'
    current_datetime = datetime.today().strftime('%Y%m%d%H%M%S')
    codTrans = 'TESTPS_' + current_datetime
    divisa = 'EUR'
    importo = round(total * 100 * 0.30, 0)
    importo = int(importo)

    # Calcolo MAC
    codtras_str = 'codTrans=' + str(codTrans)
    divisa_str = 'divisa=' + str(divisa)
    import_str = 'importo=' + str(importo)
    chiave_str = str(CHIAVESEGRETA_TEST)
    mac_str = codtras_str + divisa_str + import_str + chiave_str
    mac = hashlib.sha1(mac_str.encode('utf8')).hexdigest()

    # URLs
    merchantServerUrl = "https://transferslux.com"
    # PROD
    # NEXI_HOST = "https://ecommerce.nexi.it"
    # TEST
    NEXI_HOST = "https://int-ecommerce.nexi.it"
    requestUrl = f"{NEXI_HOST}/ecomm/ecomm/DispatcherServlet"
    success_url = urljoin(merchantServerUrl, "success/")
    cancel_url = urljoin(merchantServerUrl, "error/")

    # Update session query
    request.session['search_query'].update({
        'alias': ALIAS_TEST,
        'importo': importo,
        'divisa': divisa,
        'requestUrl': requestUrl,
        'codTrans': codTrans,
        'url': success_url,
        'url_back': cancel_url,
        'mac': mac,
        'total': total,
    })
    # Urls
    x_url = "?" + urlencode(query)
    success_url = urljoin(merchantServerUrl, "success/") + x_url
    request.session['search_query'].update({
        'alias': ALIAS_TEST,
        'importo': importo,
        'divisa': divisa,
        'requestUrl': requestUrl,
        'codTrans': codTrans,
        'url': success_url,
        'url_back': cancel_url,
        'mac': mac,
        'total': total,
    })
    request.session.modified = True
    # Context render
    context = {
        'from_short': query.get('from_short'),
        'from_hidden': query.get('from_hidden'),
        'to_short': query.get('to_short'),
        'to_hidden': query.get('to_hidden'),
        'car_class': query.get('car_class'),
        'rate': rate,
        'total': total,
        'distance': query.get('distance'),
        'travel_time': query.get('travel_time'),
        'to_date': query.get('to_date'),
        'to_time': query.get('to_time'),
        'name': name,
        'lastname': lastname,
        'alias': ALIAS_TEST,
        'importo': importo,
        'divisa': divisa,
        'requestUrl': requestUrl,
        'codTrans': codTrans,
        'url': success_url,
        'url_back': cancel_url,
        'mac': mac,
    }
    return render(request, 'booking/booking-payment.html', context)


def payment_success(request):
    terms_ = bool(request.POST.get("terms"))

    billing_data = {
        "name": request.POST.get("billing_name"),
        "lastname": request.POST.get("billing_lastname"),
        "company": request.POST.get("billing_company"),
        "address": request.POST.get("billing_address"),
    }

    transaction_data = {
        "codTrans": request.GET.get('codTrans'),
        "importo": request.GET.get('importo'),
        "data": request.GET.get('data'),
        "orario": request.GET.get('orario'),
        "codAut": request.GET.get('codAut'),
        "mac": request.GET.get('mac'),
        "divisa": 'EUR',
    }

    # Check if all required params are present
    required_params = ['codTrans',
                       'importo',
                       'data',
                       'orario',
                       'codAut',
                       'mac']
    if not all(transaction_data.get(param) for param in required_params):
        raise ValueError("Missing required parameters")

    # Calculate MAC
    # PROD
    # CHIAVESEGRETA_TEST = '9086Wh56532BG7oV6giEUW2510201H68WAqc831G'
    # TEST
    CHIAVESEGRETA_TEST = 'Y665ESJRJEK38D6D1MJJGCYAUQR2J8SV'
    mac_str = (f"codTrans={transaction_data['codTrans']}"
               f"esito=OK"
               f"importo={transaction_data['importo']}"
               f"divisa={transaction_data['divisa']}"
               f"data={transaction_data['data']}"
               f"orario={transaction_data['orario']}"
               f"codAut={transaction_data['codAut']}"
               f"{CHIAVESEGRETA_TEST}")
    mac_calculated = hashlib.sha1(mac_str.encode('utf8')).hexdigest()

    if mac_calculated != transaction_data['mac']:
        raise ValueError('MAC mismatch error')

    # Handle booking information
    if request.session.get('search_query'):
        query = request.session['search_query']
        booking_data = {
            'session_id': query.get('session_id'),
            'from_short': query.get('from_short'),
            'from_hidden': query.get('from_hidden'),
            'to_short': query.get('to_short'),
            'to_hidden': query.get('to_hidden'),
            'to_date': query.get('to_date'),
            'to_time': query.get('to_time'),
            'car_class': query.get('car_class'),
            'rate': query.get('rate'),
            'flight': query.get('flight'),
            'distance': query.get('distance'),
            'travel_time': query.get('travel_time'),
            'child_seat': query.get('child_seat'),
            'booster_seat': query.get('booster_seat'),
            'flowers': query.get('flowers'),
            'notes_extra': query.get('notes_extra', ''),
            'name': query.get('name'),
            'lastname': query.get('lastname'),
            'email': query.get('email'),
            'phone': query.get('phone'),
            'passengers': query.get('passengers'),
            'luggage': query.get('luggage'),
            'notes_details': query.get('notes_details', ''),
            'billing_name': billing_data['name'],
            'billing_lastname': billing_data['lastname'],
            'billing_company': billing_data['company'],
            'billing_address': billing_data['address'],
            'terms': terms_
        }

        # Save Booking
        instance = Booking(**booking_data)
        instance.save()

        # Retrieve booking ID
        session_id = query.get('session_id')
        booking_data = Booking.objects.get(session_id=session_id)
        # breakpoint()
        field_name = booking_data._meta.fields[0].name
        # print(field_name)
        booking_id = getattr(booking_data, field_name)

        # Update notes_details with notes_extra
        notes_details = query.get('notes_details', '')
        notes_extra = query.get('notes_extra', '')
        notes_details_upd = notes_details + '\n' + notes_extra

        # Prepare context for emails and response
        context = {
            'session_id': query.get('session_id'),
            'from_short': query.get('from_short'),
            'from_hidden': query.get('from_hidden'),
            'to_short': query.get('to_short'),
            'to_hidden': query.get('to_hidden'),
            'to_date': query.get('to_date'),
            'to_time': query.get('to_time'),
            'car_class': query.get('car_class'),
            'rate': query.get('rate'),
            'flight': query.get('flight'),
            'distance': query.get('distance'),
            'travel_time': query.get('travel_time'),
            'child_seat': query.get('child_seat'),
            'booster_seat': query.get('booster_seat'),
            'flowers': query.get('flowers'),
            'notes_extra': query.get('notes_extra', ''),
            'name': query.get('name'),
            'lastname': query.get('lastname'),
            'email': query.get('email'),
            'phone': query.get('phone'),
            'passengers': query.get('passengers'),
            'luggage': query.get('luggage'),
            'notes_details': notes_details_upd,
            'billing_name': billing_data['name'],
            'billing_lastname': billing_data['lastname'],
            'billing_company': billing_data['company'],
            'billing_address': billing_data['address'],
            'terms': terms_,
            'booking_id': booking_id
        }

        # Get language code
        language_code = get_language_from_request(request)
        subjects = {
            'it': 'La tua prenotazione è stata inviata con successo',
            'fr': 'Votre réservation a été soumise avec succès',
            'es': 'Su reserva fue enviada exitosamente',
            'ru': 'Ваше бронирование было успешно отправлено',
            'en': 'Your booking was submitted successfully'
        }
        subject = subjects.get(language_code,
                               'Your booking was submitted successfully')

        # Admin email
        admin_subject = 'Подтверждение бронирования (для админа)'
        admin_email_content = render_to_string('email/email.html', context)
        email_message = EmailMultiAlternatives(admin_subject,
                                               'autistasobrio@gmail.com',
                                               'support@transferslux.com',
                                               'support@transferslux.com')
        email_message.content_subtype = 'html'
        email_message.send()

        # Customer email
        customer_email_content = render_to_string('email/email.html', context)
        customer_email = query.get('email')
        email_message = EmailMultiAlternatives(subject,
                                               customer_email_content,
                                               customer_email,
                                               'support@transferslux.com')
        email_message.content_subtype = 'html'
        email_message.send()
        return render(request, 'booking/booking-received.html', context)

    else:
        return render(request, 'booking/booking-error.html',
                      {'error': 'Booking data not found in session'})


def payment_error(request):
    pass


def test(request):
    pass


def about(request):
    return render(request, 'about.html')


def privacy(request):
    return render(request, 'privacy-policy.html')


def terms(request):
    return render(request, 'terms-and-conditions.html')


def help(request):
    return render(request, 'help-center.html')


def contacts(request):
    return render(request, 'contacts.html')


def page_not_found(request, exception):
    return render(request, '404.html', {'path': request.path}, status=404)
