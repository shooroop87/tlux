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
from django.core.mail import EmailMultiAlternatives
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.utils.translation import get_language_from_request

google_api_key = settings.GOOGLE_MAPS_API_KEY


def index(request):
    if request.method == 'POST':
        form = SearchForm(request.POST)
        # breakpoint()
        # print(form)
        if form.is_valid():
            from_short = form.cleaned_data["from_short"]
            from_hidden = form.cleaned_data["from_hidden"]
            to_short = form.cleaned_data["to_short"]
            to_hidden = form.cleaned_data["to_hidden"]
            to_date = form.cleaned_data["to_date"]
            to_time = form.cleaned_data["to_time"]
            session_id = uuid.uuid4()
            # Create a dictionary with the fields
            query = {
                'from_short': from_short,
                'from_hidden': from_hidden,
                'to_short': to_short,
                'to_hidden': to_hidden,
                'to_date': to_date,
                'to_time': to_time,
                'session_id': str(session_id),
            }
            # print(query)
            # breakpoint()

            # Store the query in the session
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
        checked_from = 'False'
        checked_to = 'False'
        checked = 'False'
        for item in milan_bergamo_rule:
            match_from = re.search(item, from_hidden)
            if match_from:
                checked_from = 'True'
            match_to = re.search(item, to_hidden)
            if match_to:
                checked_to = 'True'
            if (checked_from == 'True' and checked_to == 'True'):
                checked = 'True'
        if checked == 'True':
            cost = 100
        if cost <= 50:
            cost_e = 50
            cost_s = 50 * 1.5
            cost_v = 50 * 1.2
        else:
            cost_e = cost
            cost_s = cost * 1.5
            cost_v = cost * 1.2
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
        query = {
            'from_short': from_short,
            'from_hidden': from_hidden,
            'to_short': to_short,
            'to_hidden': to_hidden,
            'distance': distance_km,
            'travel_time': travel_time,
            'to_date': to_date,
            'to_time': to_time,
            'session_id': session_id
        }
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
            # Query
            query = request.session['search_query']
            # Access individual fields from the dictionary
            from_short = query.get('from_short')
            from_hidden = query.get('from_hidden')
            to_short = query.get('to_short')
            to_hidden = query.get('to_hidden')
            to_short = query.get('to_short')
            to_short = query.get('to_short')
            distance = query.get('distance')
            travel_time = query.get('travel_time')
            to_date = query.get('to_date')
            to_time = query.get('to_time')
            session_id = query.get('session_id')
            context = {
                'from_short': from_short,
                'from_hidden': from_hidden,
                'to_short': to_short,
                'to_hidden': to_hidden,
                'distance': distance,
                'travel_time': travel_time,
                'to_date': to_date,
                'to_time': to_time,
                'car_class': car_class,
                'rate': rate
            }
            # Create a dictionary with the fields
            query = {
                'from_short': from_short,
                'from_hidden': from_hidden,
                'to_short': to_short,
                'to_hidden': to_hidden,
                'car_class': car_class,
                'rate': rate,
                'to_date': to_date,
                'to_time': to_time,
                'distance': distance,
                'travel_time': travel_time,
                'session_id': session_id
            }
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
            query = request.session['search_query']
            # Access individual fields from the dictionary
            from_short = query.get('from_short')
            from_hidden = query.get('from_hidden')
            to_short = query.get('to_short')
            to_hidden = query.get('to_hidden')
            car_class = query.get('car_class')
            rate = query.get('rate')
            distance = query.get('distance')
            travel_time = query.get('travel_time')
            to_date = query.get('to_date')
            to_time = query.get('to_time')
            session_id = query.get('session_id')
            cst = int(child_seat) * 15
            bst = int(booster_seat) * 20
            fl = int(flowers) * 70
            extra_total = int(cst) + int(bst) + int(fl)
            rate = str(rate).replace(',', '.')
            total = float(rate) + float(extra_total)
            # Create a dictionary with the fields
            query = {
                'from_short': from_short,
                'from_hidden': from_hidden,
                'to_short': to_short,
                'to_hidden': to_hidden,
                'car_class': car_class,
                'rate': rate,
                'total': total,
                'child_seat_total': cst,
                'booster_seat_total': bst,
                'flowers_total': fl,
                'extra_total': extra_total,
                'distance': distance,
                'travel_time': travel_time,
                'to_date': to_date,
                'to_time': to_time,
                'flight': flight,
                'child_seat': child_seat,
                'booster_seat': booster_seat,
                'flowers': flowers,
                'notes_extra': notes_extra,
                'session_id': session_id
            }
            context = {
                'from_short': from_short,
                'from_hidden': from_hidden,
                'to_short': to_short,
                'to_hidden': to_hidden,
                'car_class': car_class,
                'rate': rate,
                'total': total,
                'child_seat_total': cst,
                'booster_seat_total': bst,
                'flowers_total': fl,
                'extra_total': extra_total,
                'distance': distance,
                'travel_time': travel_time,
                'to_date': to_date,
                'to_time': to_time,
                'flight': flight,
                'child_seat': child_seat,
                'booster_seat': booster_seat,
                'flowers': flowers,
                'notes_extra': notes_extra,
            }
            # Store the query in the session
            request.session['search_query'] = query
            return render(request, 'booking/booking-passenger.html', context)

    # Query
    query = request.session['search_query']
    # Access individual fields from the dictionary
    from_short = query.get('from_short')
    from_hidden = query.get('from_hidden')
    to_short = query.get('to_short')
    to_hidden = query.get('to_hidden')
    car_class = query.get('car_class')
    rate = query.get('rate')
    distance = query.get('distance')
    travel_time = query.get('travel_time')
    to_date = query.get('to_date')
    to_time = query.get('to_time')
    session_id = query.get('session_id')
    context = {
        'from_short': from_short,
        'from_hidden': from_hidden,
        'to_short': to_short,
        'to_hidden': to_hidden,
        'car_class': car_class,
        'rate': rate,
        'distance': distance,
        'travel_time': travel_time,
        'to_date': to_date,
        'to_time': to_time,
    }
    return render(request, 'booking/booking-passenger.html', context)


def payment(request):
    if request.method == 'POST':
        form = DetailsForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data["name"]
            lastname = form.cleaned_data["lastname"]
            email = form.cleaned_data["email"]
            phone = form.cleaned_data["phone"]
            passengers = form.cleaned_data["passengers"]
            luggage = form.cleaned_data["luggage"]
            notes_details = form.cleaned_data["notes_details"]
            # Query
            query = request.session['search_query']
            # Access individual fields from the dictionary
            from_short = query.get('from_short')
            from_hidden = query.get('from_hidden')
            to_short = query.get('to_short')
            to_hidden = query.get('to_hidden')
            to_date = query.get('to_date')
            to_time = query.get('to_time')
            car_class = query.get('car_class')
            rate = query.get('rate')
            total = query.get('total')
            distance = query.get('distance')
            travel_time = query.get('travel_time')
            flight = query.get('flight')
            child_seat = query.get('child_seat')
            booster_seat = query.get('booster_seat')
            flowers = query.get('flowers')
            notes_extra = query.get('notes_extra')
            session_id = query.get('session_id')
            # Get transactions
            ALIAS_TEST = query.get('alias')
            total = str(total).replace(',', '.')
            importo = float(total)
            divisa = query.get('divisa')
            codTrans = query.get('codTrans')
            requestUrl = query.get('requestUrl')
            success_url = query.get('success_url')
            cancel_url = query.get('cancel_url')
            mac = query.get('mac')
            # Create a dictionary with the fields1
            query = {
                'from_short': from_short,
                'from_hidden': from_hidden,
                'to_short': to_short,
                'to_hidden': to_hidden,
                'car_class': car_class,
                'rate': rate,
                'distance': distance,
                'travel_time': travel_time,
                'to_date': to_date,
                'to_time': to_time,
                'flight': flight,
                'child_seat': child_seat,
                'booster_seat': booster_seat,
                'flowers': flowers,
                'notes_extra': notes_extra,
                'name': name,
                'lastname': lastname,
                'email': email,
                'phone': phone,
                'passengers': passengers,
                'luggage': luggage,
                'notes_details': notes_details,
                'session_id': session_id,
                'alias': ALIAS_TEST,
                'importo': importo,
                'divisa': divisa,
                'codTrans': codTrans,
                'requestUrl': requestUrl,
                'url': success_url,
                'url_back': cancel_url,
                'mac': mac,
            }
            context = {
                'from_short': from_short,
                'from_hidden': from_hidden,
                'to_short': to_short,
                'to_hidden': to_hidden,
                'car_class': car_class,
                'rate': rate,
                'distance': distance,
                'travel_time': travel_time,
                'to_date': to_date,
                'to_time': to_time,
                'flight': flight,
                'child_seat': child_seat,
                'booster_seat': booster_seat,
                'flowers': flowers,
                'notes_extra': notes_extra,
                'name': name,
                'lastname': lastname,
                'email': email,
                'phone': phone,
                'passengers': passengers,
                'luggage': luggage,
                'notes_details': notes_details,
                'alias': ALIAS_TEST,
                'importo': importo,
                'divisa': divisa,
                'codTrans': codTrans,
                'requestUrl': requestUrl,
                'url': success_url,
                'url_back': cancel_url,
                'mac': mac,
            }
            # Store the query in the session
            request.session['search_query'] = query
    # If not post show page
    name = request.POST.get("name")
    lastname = request.POST.get("lastname")
    query = request.session['search_query']
    from_short = query.get('from_short')
    from_hidden = query.get('from_hidden')
    to_short = query.get('to_short')
    to_hidden = query.get('to_hidden')
    to_date = query.get('to_date')
    to_time = query.get('to_time')
    car_class = query.get('car_class')
    rate = query.get('rate')
    total = query.get('total')
    if total is None:
        total = '0'
    total = str(total).replace(',', '.')
    total = float(total)
    importo = round(total * 100 * 0.30, 0)
    importo = int(importo)
    distance = query.get('distance')
    travel_time = query.get('travel_time')
    # Settings
    ALIAS_TEST = 'ALIAS_WEB_00082258'
    CHIAVESEGRETA_TEST = 'Y665ESJRJEK38D6D1MJJGCYAUQR2J8SV'
    current_datetime = datetime.today().strftime('%Y%m%d%H%M%S')
    codTrans = 'TESTPS_' + current_datetime
    divisa = 'EUR'
    # Calcolo MAC
    codtras_str = 'codTrans=' + str(codTrans)
    divisa_str = 'divisa=' + str(divisa)
    import_str = 'importo=' + str(importo)
    chiave_str = str(CHIAVESEGRETA_TEST)
    mac_str = codtras_str + divisa_str + import_str + chiave_str
    mac = hashlib.sha1(mac_str.encode('utf8')).hexdigest()
    # Payment gateway
    HTTP_HOST = "http://transferslux.com"
    NEXI_HOST = "https://int-ecommerce.nexi.it"
    requestUrl = NEXI_HOST + "/ecomm/ecomm/DispatcherServlet"
    XPAY_LINK = "/xpay/pagamento_semplice_python/codice_base/"
    merchantServerUrl = HTTP_HOST + XPAY_LINK
    request.session['search_query'].update({
        'alias': ALIAS_TEST,
        'importo': importo,
        'divisa': divisa,
        'requestUrl': requestUrl,
        'merchantServerUrl': merchantServerUrl,
        'codTrans': codTrans,
        'url': success_url,
        'url_back': cancel_url,
        'mac': mac,
    })
    request.session.modified = True
    # Urls
    x_url = "?" + urlencode(query)
    success_url = urljoin(merchantServerUrl, "success/") + x_url
    cancel_url = urljoin(merchantServerUrl, "error/")
    context = {
        'from_short': from_short,
        'from_hidden': from_hidden,
        'to_short': to_short,
        'to_hidden': to_hidden,
        'car_class': car_class,
        'rate': rate,
        'distance': distance,
        'travel_time': travel_time,
        'to_date': to_date,
        'to_time': to_time,
        'name': name,
        'lastname': lastname,
        'alias': ALIAS_TEST,
        'importo': importo,
        'divisa': divisa,
        'requestUrl': requestUrl,
        'merchantServerUrl': merchantServerUrl,
        'codTrans': codTrans,
        'url': success_url,
        'url_back': cancel_url,
        'mac': mac,
    }
    return render(request, 'booking/booking-payment.html', context)


def payment_success(request):
    terms = request.POST.get("terms")
    if terms == 'on':
        terms_ = True
    else:
        terms_ = False
    billing_name = request.POST.get("billing_name")
    billing_lastname = request.POST.get("billing_lastname")
    billing_company = request.POST.get("billing_company")
    billing_address = request.POST.get("billing_address")
    # Query
    query = request.session['search_query']
    from_short = query.get('from_short')
    from_hidden = query.get('from_hidden')
    to_short = query.get('to_short')
    to_hidden = query.get('to_hidden')
    to_date = query.get('to_date')
    to_time = query.get('to_time')
    car_class = query.get('car_class')
    rate = query.get('rate')
    total = query.get('total')
    child_seat_total = query.get('child_seat_total')
    booster_seat_total = query.get('booster_seat_total')
    flowers_total = query.get('flowers_total')
    extra_total = query.get('extra_total')
    distance = query.get('distance')
    travel_time = query.get('travel_time')
    flight = query.get('flight')
    child_seat = query.get('child_seat')
    booster_seat = query.get('booster_seat')
    flowers = query.get('flowers')
    notes_extra = query.get('notes_extra')
    name = query.get('name')
    lastname = query.get('lastname')
    email = query.get('email')
    phone = query.get('phone')
    passengers = query.get('passengers')
    luggage = query.get('luggage')
    notes_details = query.get('notes_details')
    session_id = query.get('session_id')
    # Save Booking
    instance = Booking(
        session_id=session_id,
        from_hidden=from_hidden,
        to_hidden=to_hidden,
        from_short=from_short,
        to_short=to_short,
        to_date=to_date,
        to_time=to_time,
        distance=distance,
        travel_time=travel_time,
        car_class=car_class,
        rate=rate,
        flight=flight,
        child_seat=child_seat,
        booster_seat=booster_seat,
        flowers=flowers,
        notes_extra=notes_extra,
        name=name,
        lastname=lastname,
        email=email,
        phone=phone,
        passengers=passengers,
        luggage=luggage,
        notes_details=notes_details,
        billing_name=billing_name,
        billing_lastname=billing_lastname,
        billing_company=billing_company,
        billing_address=billing_address,
        terms=terms_
    )
    instance.save()
    # Get booking ID
    booking_data = Booking.objects.get(session_id=session_id)
    # breakpoint()
    field_name = booking_data._meta.fields[0].name
    # print(field_name)
    booking_id = getattr(booking_data, field_name)
    # print(booking_id)
    # Make context
    notes_details = notes_details + '\n' + notes_extra
    context = {
        'booking_id': booking_id,
        'session_id': session_id,
        'from_short': from_short,
        'from_hidden': from_hidden,
        'to_short': to_short,
        'to_hidden': to_hidden,
        'car_class': car_class,
        'rate': rate,
        'total': total,
        'child_seat_total': child_seat_total,
        'booster_seat_total': booster_seat_total,
        'flowers_total': flowers_total,
        'extra_total': extra_total,
        'distance': distance,
        'travel_time': travel_time,
        'to_date': to_date,
        'to_time': to_time,
        'flight': flight,
        'child_seat': child_seat,
        'booster_seat': booster_seat,
        'flowers': flowers,
        'notes_extra': notes_extra,
        'name': name,
        'lastname': lastname,
        'email': email,
        'phone': phone,
        'passengers': passengers,
        'luggage': luggage,
        'notes_details': notes_details,
        'billing_name': billing_name,
        'billing_lastname': billing_lastname,
        'billing_company': billing_company,
        'billing_address': billing_address,
        'terms': terms
    }
    # Генерация PDF и сохранение в MEDIA_ROOT
    # str_id = str(session_id)
    # voucher_name = f"voucher_{str_id}.pdf"
    language_code = get_language_from_request(request)
    if language_code == 'it':
        subject = 'La tua prenotazione è stata inviata con successo'
    elif language_code == 'fr':
        subject = 'Votre réservation a été soumise avec succès'
    elif language_code == 'es':
        subject = 'Su reserva fue enviada exitosamente'
    elif language_code == 'ru':
        subject = 'Ваше бронирование было успешно отправлено'
    else:
        subject = 'Your booking was submitted successfully'
    from_email = settings.DEFAULT_FROM_EMAIL
    to = [email, from_email]
    # Рендеринг HTML-шаблона1
    html_content = render_to_string('email/email.html', context)
    email_message = EmailMultiAlternatives(subject,
                                           html_content,
                                           from_email,
                                           to=to)
    email_message.content_subtype = 'html'
    email_message.send()
    return render(request, 'booking/booking-received.html', context)


def payment_success(request):
    terms = request.POST.get("terms")
    if terms == 'on':
        terms_ = True
    else:
        terms_ = False
    billing_name = request.POST.get("billing_name")
    billing_lastname = request.POST.get("billing_lastname")
    billing_company = request.POST.get("billing_company")
    billing_address = request.POST.get("billing_address")
    # Transaction
    codTrans = request.GET.get('codTrans')
    importo = request.GET.get('importo')
    data = request.GET.get('data')
    orario = request.GET.get('orario')
    codAut = request.GET.get('codAut')
    divisa = 'EUR'
    mac = request.GET.get('mac')
    CHIAVESEGRETA_TEST = 'Y665ESJRJEK38D6D1MJJGCYAUQR2J8SV'
    param_from_request = {
        "codTrans": codTrans,
        "esito": "OK",
        "importo": importo,
        "divisa": divisa,
        "data": data,
        "orario": orario,
        "codAut": codAut,
        "mac": mac,
    }
    requiredParams = ['codTrans',
                      'esito',
                      'importo',
                      'divisa',
                      'data',
                      'orario',
                      'codAut',
                      'mac']
    for param in requiredParams:
        if param not in param_from_request:
            raise ValueError("Parametro {} mancante".format(param))
    # Calcolo MAC con i parametri di ritorno
    mac_str = 'codTrans=' + param_from_request['codTrans'] + \
        'esito=' + param_from_request['esito'] + \
        'importo=' + param_from_request['importo'] + \
        'divisa=' + param_from_request['divisa'] + \
        'data=' + param_from_request['data'] + \
        'orario=' + param_from_request['orario'] + \
        'codAut=' + param_from_request['codAut'] + \
        CHIAVESEGRETA_TEST
    macCalculated = hashlib.sha1(mac_str.encode('utf8')).hexdigest()
    # Verifico corrispondeza MAC
    if macCalculated != param_from_request['mac']:
        raise ValueError('Errore MAC')
    # Nel caso in cui non ci siano errori gestisco il parametro esito
    if param_from_request['esito'] == 'OK':
        print('Transazione andato bene!')
    # Query
    query = request.session['search_query']
    from_short = query.get('from_short')
    from_hidden = query.get('from_hidden')
    to_short = query.get('to_short')
    to_hidden = query.get('to_hidden')
    to_date = query.get('to_date')
    to_time = query.get('to_time')
    car_class = query.get('car_class')
    rate = query.get('rate')
    total = query.get('total')
    child_seat_total = query.get('child_seat_total')
    booster_seat_total = query.get('booster_seat_total')
    flowers_total = query.get('flowers_total')
    extra_total = query.get('extra_total')
    distance = query.get('distance')
    travel_time = query.get('travel_time')
    flight = query.get('flight')
    child_seat = query.get('child_seat')
    booster_seat = query.get('booster_seat')
    flowers = query.get('flowers')
    notes_extra = query.get('notes_extra')
    name = query.get('name')
    lastname = query.get('lastname')
    email = query.get('email')
    phone = query.get('phone')
    passengers = query.get('passengers')
    luggage = query.get('luggage')
    notes_details = query.get('notes_details')
    session_id = query.get('session_id')
    # Save Booking
    instance = Booking(
        session_id=session_id,
        from_hidden=from_hidden,
        to_hidden=to_hidden,
        from_short=from_short,
        to_short=to_short,
        to_date=to_date,
        to_time=to_time,
        distance=distance,
        travel_time=travel_time,
        car_class=car_class,
        rate=rate,
        flight=flight,
        child_seat=child_seat,
        booster_seat=booster_seat,
        flowers=flowers,
        notes_extra=notes_extra,
        name=name,
        lastname=lastname,
        email=email,
        phone=phone,
        passengers=passengers,
        luggage=luggage,
        notes_details=notes_details,
        billing_name=billing_name,
        billing_lastname=billing_lastname,
        billing_company=billing_company,
        billing_address=billing_address,
        terms=terms_
    )
    instance.save()
    # Get booking ID
    booking_data = Booking.objects.get(session_id=session_id)
    # breakpoint()
    field_name = booking_data._meta.fields[0].name
    # print(field_name)
    booking_id = getattr(booking_data, field_name)
    # print(booking_id)
    # Make context
    notes_details = notes_details + '\n' + notes_extra
    context = {
        'booking_id': booking_id,
        'session_id': session_id,
        'from_short': from_short,
        'from_hidden': from_hidden,
        'to_short': to_short,
        'to_hidden': to_hidden,
        'car_class': car_class,
        'rate': rate,
        'total': total,
        'child_seat_total': child_seat_total,
        'booster_seat_total': booster_seat_total,
        'flowers_total': flowers_total,
        'extra_total': extra_total,
        'distance': distance,
        'travel_time': travel_time,
        'to_date': to_date,
        'to_time': to_time,
        'flight': flight,
        'child_seat': child_seat,
        'booster_seat': booster_seat,
        'flowers': flowers,
        'notes_extra': notes_extra,
        'name': name,
        'lastname': lastname,
        'email': email,
        'phone': phone,
        'passengers': passengers,
        'luggage': luggage,
        'notes_details': notes_details,
        'billing_name': billing_name,
        'billing_lastname': billing_lastname,
        'billing_company': billing_company,
        'billing_address': billing_address,
        'terms': terms
    }
    # Генерация PDF и сохранение в MEDIA_ROOT
    # str_id = str(session_id)
    # voucher_name = f"voucher_{str_id}.pdf"
    language_code = get_language_from_request(request)
    if language_code == 'it':
        subject = 'La tua prenotazione è stata inviata con successo'
    elif language_code == 'fr':
        subject = 'Votre réservation a été soumise avec succès'
    elif language_code == 'es':
        subject = 'Su reserva fue enviada exitosamente'
    elif language_code == 'ru':
        subject = 'Ваше бронирование было успешно отправлено'
    else:
        subject = 'Your booking was submitted successfully'
    from_email = settings.DEFAULT_FROM_EMAIL
    to = [email, from_email]
    # Рендеринг HTML-шаблона1
    html_content = render_to_string('email/email.html', context)
    email_message = EmailMultiAlternatives(subject,
                                           html_content,
                                           from_email,
                                           to=to)
    email_message.content_subtype = 'html'
    email_message.send()
    return render(request, 'booking/booking-received.html', context)


def payment_error(request):
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
