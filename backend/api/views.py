import hashlib
import math
import re
import sys
import uuid
from datetime import datetime
from urllib.parse import urljoin
import logging

logger = logging.getLogger(__name__)

if sys.version_info >= (3,):
    from urllib.parse import urlencode  # noqa: F401
else:
    from urllib import urlencode  # type: ignore  # noqa: F401

import googlemaps
from api.forms import DetailsForm, ExtrasForm, SearchForm, VehicleForm
from api.models import Booking, Search
from django.http import HttpResponse
from django.conf import settings
from django.contrib import messages
from django.views.decorators.cache import cache_page
from django.core.mail import EmailMultiAlternatives
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.utils.translation import get_language_from_request
from django.utils.html import strip_tags

google_directions_key = settings.GOOGLE_DIRECTIONS_KEY


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
                'ru': 'Пожалуйста, заполните все обязательные поля',
                'en': 'Please fill in all required fields'
            }
            error_message = errors.get(language_code, 'Please fill in all required fields')
            # Если поля не заполнены, вернуть ошибку
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


def vehicle(request):  # noqa: C901
    if 'search_query' not in request.session:
        return redirect('api:index')

    query = request.session['search_query']
    # Access individual fields from the dictionary
    from_short = query.get('from_short')
    from_hidden = query.get('from_hidden')
    to_short = query.get('to_short')
    to_hidden = query.get('to_hidden')

    # Добавь это для отладки
    print("="*50)
    print(f"FROM_HIDDEN: '{from_hidden}'")
    print(f"TO_HIDDEN: '{to_hidden}'")
    print("="*50)

    to_date = query.get('to_date')
    to_time = query.get('to_time')
    session_id = query.get('session_id')
    # Perform your search logic here based on the query
    gmaps = googlemaps.Client(key=google_directions_key)
    # Шаблон для Милана, учитывающий разные написания
    mp = re.compile(
        r'(milan|milano|милан)',
        re.IGNORECASE
    )
    # Шаблон для Бергамо, учитывающий различные варианты написания
    bp = re.compile(
        r'(bergamo|бергамо|orio al serio|bgy|'
        r'аэропорт\sбергамо|via aeroporto.*orio al serio|'
        r'airport|аэропорт|aeroporto)',
        re.IGNORECASE
    )
    # Шаблон для Мальпенсы, учитывающий различные варианты написания
    ap = re.compile(
        r'(malpensa|мальпенса|малпенса|mxp|'
        r'аэропорт\sмальпенса|aeroporto di milano malpensa|'
        r'malpensa\sairport|milan malpensa airport|'
        r'airport|аэропорт|aeroporto)',
        re.IGNORECASE
    )
    # Шаблон для Мальпенсы - но Ферно Варезе
    fv = re.compile(
        r'(21010\sФерно,\sВарезе,\sИталия|'
        r'21010\sFerno,\sVarese,\sItaly|'
        r'21010\sFerno,\sVarese,\sItalia)',
        re.IGNORECASE
    )
    zm = re.compile(
        r'(3920\sЦерматт,\sШвейцария|'
        r'3920\sZermatt,\sSwitzerland|'
        r'3920\sZermatt,\sSvizzera)',
        re.IGNORECASE
    )
    geneva = re.compile(
        r'(geneva|женева|gva|geneva airport|'
        r'аэропорт\sженева|aeroport de geneve|'
        r'genève|aéroport de genève)',
        re.IGNORECASE
    )
    lyon = re.compile(
        r'(lyon|лион|lys|lyon airport|'
        r'аэропорт\sлион|aeroport de lyon)',
        re.IGNORECASE)
    courchevel = re.compile(
        r'(courchevel|куршевель)',
        re.IGNORECASE)
    # Замена адресов, если они относятся к Церматт
    try:
        if zm.search(from_hidden or ""):
            from_hidden_adj = "Hofstrasse 40, 4000 Täsch, Svizzera"
            directions_result = gmaps.directions(
                origin=from_hidden_adj,
                destination=to_hidden,
                mode="driving",
                departure_time="now",
                traffic_model="best_guess"
            )
        elif zm.search(to_hidden or ""):
            to_hidden_adj = "Hofstrasse 40, 4000 Täsch, Svizzera"
            directions_result = gmaps.directions(
                origin=from_hidden,
                destination=to_hidden_adj,
                mode="driving",
                departure_time="now",
                traffic_model="best_guess"
            )
        else:
            directions_result = gmaps.directions(
                origin=from_hidden,
                destination=to_hidden,
                mode="driving",
                departure_time="now",
                traffic_model="best_guess"
            )
    except Exception as e:
        logger.exception("Google Maps directions error: %s", e)
        directions_result = None

    km = 0.0
    travel_time = ""
    cost = 0

    if directions_result:
        try:
            route = directions_result[0]['legs'][0]
            km = round(route['distance']['value'] / 1000, 1)
            travel_time = route['duration']['text']
            # Расчёт базовой стоимости по километражу
            base_cost_per_km = 2  # Стоимость за километр
            cost = math.ceil(km * base_cost_per_km)
        except Exception as e:
            logger.exception("Failed to parse route: %s", e)

    # Проверка на маршруты к/из аэропортов
    # Из Милана в Бергамо и наоборот
    if (mp.search(from_hidden or "") and bp.search(to_hidden or "")) and km <= 70:
        cost = 100
    elif (bp.search(from_hidden or "") and mp.search(to_hidden or "")) and km <= 70:
        cost = 100
    # Из Милана в аэропорт и наоборот
    elif (mp.search(from_hidden or "") and ap.search(to_hidden or "")) and km <= 70:
        cost = 100
    elif (ap.search(from_hidden or "") and mp.search(to_hidden or "")) and km <= 70:
        cost = 100
    # Из Милана в Ферно Верезе
    elif (mp.search(from_hidden or "") and fv.search(to_hidden or "")) and km <= 70:
        cost = 100
    elif (fv.search(from_hidden or "") and mp.search(to_hidden or "")) and km <= 70:
        cost = 100
    else:
        logger.info("Стоимость рассчитывается по километражу.")

    # Дополнительные классы автомобилей
    if (geneva.search(from_hidden or "") and courchevel.search(to_hidden or "")) or (courchevel.search(from_hidden or "") and geneva.search(to_hidden or "")):  # noqa: E501
        cost_e = 500  # Седан
        cost_v = 550  # Минибус
        cost_s = 750  # S-класс
    elif (lyon.search(from_hidden or "") and courchevel.search(to_hidden or "")) or (courchevel.search(from_hidden or "") and lyon.search(to_hidden or "")):  # noqa: E501
        cost_e = 500  # Седан
        cost_v = 550  # Минибус
        cost_s = 750  # S-класс
    else:
        # Для остальных маршрутов расчет по километражу
        cost_e = max(50, cost)
        cost_s = int(math.ceil(cost_e * 1.5))
        cost_v = int(math.ceil(cost_e * 1.2))

    context = {
        'from_short': from_short,
        'from_hidden': from_hidden,
        'to_short': to_short,
        'to_hidden': to_hidden,
        'cost_e': cost_e,
        'cost_s': cost_s,
        'cost_v': cost_v,
        'distance': km,
        'travel_time': travel_time,
        'to_date': to_date,
        'to_time': to_time,
    }
    # Update query
    query.update({'distance': km, 'travel_time': travel_time})
    request.session['search_query'] = query
    # Save search
    try:
        instance = Search(
            from_hidden=from_hidden,
            to_hidden=to_hidden,
            from_short=from_short,
            to_short=to_short,
            to_date=to_date,
            to_time=to_time,
            distance=km,
            travel_time=travel_time,
            session_id=session_id
        )
        instance.save()
    except Exception as e:
        logger.exception("Failed to save Search: %s", e)
    # Render next page
    return render(request, 'booking/booking-vehicle.html', context)


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
    # Базовые настройки Nexi (переключаются .env → settings.NEXI_ENV)
    alias = settings.NEXI_ALIAS
    secret = settings.NEXI_SECRET
    nexi_host = settings.NEXI_HOST
    nexi_env = getattr(settings, 'NEXI_ENV', 'dev').lower()

    if request.method == 'POST':
        form = DetailsForm(request.POST)
        if form.is_valid():
            # Extract form data
            cleaned_data = form.cleaned_data
            # Retrieve session data
            query = request.session.get('search_query', {})
            # Сохраняем пассажирские данные в сессию
            query.update({
                'name': cleaned_data["name"],
                'lastname': cleaned_data["lastname"],
                'email': cleaned_data["email"],
                'phone': cleaned_data["phone"],
                'passengers': cleaned_data["passengers"],
                'luggage': cleaned_data["luggage"],
                'notes_details': cleaned_data["notes_details"],
            })
            request.session['search_query'] = query

    # Retrieve session data
    query = request.session.get('search_query', {})
    if not query:
        return redirect('api:index')

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

    # Параметры платежа (Nexi принимает сумму в младших единицах, EUR→центы)
    DEPOSIT_FACTOR = 0.30  # 30% предоплата — оставь/измени по бизнес-логике
    importo = int(round(total * 100 * DEPOSIT_FACTOR, 0))
    divisa = 'EUR'
    current_datetime = datetime.today().strftime('%Y%m%d%H%M%S')
    prefix = 'PS' if nexi_env == 'prod' else 'TESTPS'
    codTrans = f'{prefix}_{current_datetime}'

    # Calcolo MAC (INIT): порядок полей важен
    mac_str = f'codTrans={codTrans}divisa={divisa}importo={importo}{secret}'
    mac = hashlib.sha1(mac_str.encode('utf8')).hexdigest()

    # URLs
    merchantServerUrl = settings.SITE_BASE_URL.rstrip("/")
    requestUrl = f"{nexi_host}/ecomm/ecomm/DispatcherServlet"
    success_url = urljoin(merchantServerUrl + "/", "success/")
    cancel_url = urljoin(merchantServerUrl + "/", "error/")

    # Update session query (один раз)
    query.update({
        'alias': alias,
        'importo': importo,
        'divisa': divisa,
        'requestUrl': requestUrl,
        'codTrans': codTrans,
        'url': success_url,
        'url_back': cancel_url,
        'mac': mac,
        'total': total,
    })
    request.session['search_query'] = query
    request.session.modified = True

    # Context render
    context = {
        'from_short': query.get('from_short'),
        'from_hidden': query.get('from_hidden'),
        'to_short': query.get('to_short'),
        'to_hidden': query.get('to_hidden'),
        'car_class': query.get('car_class'),
        'child_seat': child_seat,
        'booster_seat': booster_seat,
        'flowers': flowers,
        'extra_total': extra_total,
        'child_seat_total': cst,
        'booster_seat_total': bst,
        'flowers_total': fl,
        'rate': rate,
        'total': total,
        'distance': query.get('distance'),
        'travel_time': query.get('travel_time'),
        'to_date': query.get('to_date'),
        'to_time': query.get('to_time'),
        'name': query.get('name'),
        'lastname': query.get('lastname'),
        # Параметры формы для Nexi
        'alias': alias,
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
    # Лог входящих параметров от Nexi
    logger.info("Nexi return: method=%s GET=%s POST=%s", request.method, dict(request.GET), dict(request.POST))

    # В ответе Nexi два mac — берём последний
    mac_values = request.GET.getlist('mac') or request.POST.getlist('mac')
    mac_from_gateway = mac_values[-1] if mac_values else None

    esito = request.GET.get('esito') or request.POST.get('esito')

    terms_ = bool(request.POST.get("terms"))

    billing_data = {
        "name": request.POST.get("billing_name"),
        "lastname": request.POST.get("billing_lastname"),
        "company": request.POST.get("billing_company"),
        "address": request.POST.get("billing_address"),
    }

    transaction_data = {
        "codTrans": request.GET.get('codTrans') or request.POST.get('codTrans'),
        "importo":  request.GET.get('importo')  or request.POST.get('importo'),
        "data":     request.GET.get('data')     or request.POST.get('data'),
        "orario":   request.GET.get('orario')   or request.POST.get('orario'),
        "codAut":   request.GET.get('codAut')   or request.POST.get('codAut'),
        "mac":      mac_from_gateway,
        "divisa":  'EUR',
        "esito":    esito,
    }

    # Check if all required params are present
    required_params = ['codTrans', 'importo', 'data', 'orario', 'codAut', 'mac', 'esito']
    if not all(transaction_data.get(p) for p in required_params):
        missing = [p for p in required_params if not transaction_data.get(p)]
        logger.error("Missing required parameters: %s", missing)
        return render(request, 'booking/booking-payment-error.html',
                      {'reason': f"Missing params: {', '.join(missing)}"}, status=400)

    # Calculate MAC (callback) — берём секрет из settings, esito — из ответа
    secret = getattr(settings, "NEXI_SECRET", "")

    mac_str = (
        f"codTrans={transaction_data['codTrans']}"
        f"esito={transaction_data['esito']}"
        f"importo={transaction_data['importo']}"
        f"divisa={transaction_data['divisa']}"
        f"data={transaction_data['data']}"
        f"orario={transaction_data['orario']}"
        f"codAut={transaction_data['codAut']}"
        f"{secret}"
    )
    mac_calculated = hashlib.sha1(mac_str.encode('utf8')).hexdigest()

    if mac_calculated != transaction_data['mac']:
        logger.error("MAC mismatch: calc=%s given=%s", mac_calculated, transaction_data['mac'])
        return render(request, 'booking/booking-payment-error.html',
                      {'reason': 'MAC mismatch'}, status=400)

    if str(transaction_data['esito']).upper() != 'OK':
        logger.warning("Payment not OK: esito=%s", transaction_data['esito'])
        return render(request, 'booking/booking-payment-error.html',
                      {'reason': f"Payment status: {transaction_data['esito']}"}, status=400)

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
            'notes_extra': query.get('notes_extra'),
            'name': query.get('name'),
            'lastname': query.get('lastname'),
            'email': query.get('email'),
            'phone': query.get('phone'),
            'passengers': query.get('passengers'),
            'luggage': query.get('luggage'),
            'notes_details': query.get('notes_details'),
            'billing_name': billing_data['name'],
            'billing_lastname': billing_data['lastname'],
            'billing_company': billing_data['company'],
            'billing_address': billing_data['address'],
            'terms': terms_
        }

        # Save Booking
        try:
            instance = Booking(**booking_data)
            instance.save()
        except Exception as e:
            logger.exception("Booking save failed: %s", e)
            return render(request, 'booking/booking-payment-error.html',
                          {'reason': 'Failed to save booking'}, status=500)

        # Retrieve booking ID
        try:
            session_id = query.get('session_id')
            booking_data = Booking.objects.get(session_id=session_id)
            field_name = booking_data._meta.fields[0].name
            booking_id = getattr(booking_data, field_name)
        except Exception as e:
            logger.exception("Fetch booking id failed: %s", e)
            booking_id = None

        # Update notes_details with notes_extra
        notes_details = (query.get('notes_details') or '').strip()
        notes_extra = (query.get('notes_extra') or '').strip()
        notes_details_upd = (notes_extra + ' ' + notes_details).strip()

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
            'total': query.get('total'),
            'flight': query.get('flight'),
            'distance': query.get('distance'),
            'travel_time': query.get('travel_time'),
            'child_seat': query.get('child_seat'),
            'booster_seat': query.get('booster_seat'),
            'flowers': query.get('flowers'),
            'notes_extra': query.get('notes_extra'),
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
        subject = subjects.get(language_code, 'Your booking was submitted successfully')

        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "support@transferslux.com")
        
        # Admin email
        try:
            admin_email_content = render_to_string('email/email.html', context)
            plain_admin_html = strip_tags(admin_email_content)
            email_message = EmailMultiAlternatives(
                'Подтверждение бронирования (для админа)',
                plain_admin_html, from_email,
                ['autistasobrio@gmail.com', 'job@andreyegorov.com']
            )
            email_message.content_subtype = 'html'
            email_message.attach_alternative(admin_email_content, "text/html") 
            email_message.send()
        except Exception as e:
            logger.exception("Admin email send failed: %s", e)

        # Customer email
        try:
            customer_email_content = render_to_string('email/email.html', context)
            plain_customer_html = strip_tags(customer_email_content)
            customer = (query.get('email') or '').strip()
            if customer:
                email_message = EmailMultiAlternatives(
                    subject, plain_customer_html, from_email, [customer]
                )
                email_message.content_subtype = 'html'
                email_message.attach_alternative(customer_email_content, "text/html") 
                email_message.send()
            else:
                logger.warning("Customer email empty; skip sending")
        except Exception as e:
            logger.exception("Customer email send failed: %s", e)

        return render(request, 'booking/booking-received.html', context)

    else:
        return render(request, 'booking/booking-payment-error.html')


def payment_error(request):
    return render(request, 'booking/booking-payment-error.html')


@cache_page(60 * 60)  # 1 час
def about(request):
    return render(request, 'about.html')


@cache_page(60 * 60)
def privacy(request):
    return render(request, 'privacy-policy.html')


@cache_page(60 * 60)
def terms(request):
    return render(request, 'terms-and-conditions.html')

@cache_page(60 * 60)
def help(request):
    return render(request, 'help-center.html')

@cache_page(60 * 60)
def contacts(request):
    return render(request, 'contacts.html')


def page_not_found(request, exception):
    return render(request, '404.html', {'path': request.path}, status=404)


def internal_server_error(request, *args, **argv):
    return render(request, '500.html', status=500)


def robots_txt(request):
    lines = [
        "User-agent: *",
        "Allow: /",
        "Disallow: /dj-admin/",
        "Disallow: /booking-vehicle/",
        "Disallow: /booking-extra/",
        "Disallow: /booking-passenger/",
        "Disallow: /booking-payment/",
        "Disallow: /success/",
        "Disallow: /error/",
        "",
        "Sitemap: https://transferslux.com/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")
