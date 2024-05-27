import json
import math
import os
import re
import uuid
from datetime import datetime
from io import BytesIO

import googlemaps
from api.forms import DetailsForm, ExtrasForm, SearchForm, VehicleForm
from api.models import Booking, Search
from django.conf import settings
from django.contrib.staticfiles import finders
from django.core.mail import EmailMultiAlternatives, send_mail
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.template.loader import get_template, render_to_string
from django.utils.html import strip_tags
from xhtml2pdf import pisa

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

            # Create a dictionary with the fields
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
                'session_id': session_id
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
        # breakpoint()
        # print(form)
        # print(form.is_valid())
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
            distance = query.get('distance')
            travel_time = query.get('travel_time')
            flight = query.get('flight')
            child_seat = query.get('child_seat')
            booster_seat = query.get('booster_seat')
            flowers = query.get('flowers')
            notes_extra = query.get('notes_extra')
            session_id = query.get('session_id')

            # Create a dictionary with the fields
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
                'session_id': session_id
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
                'notes_details': notes_details
            }
            # Store the query in the session
            request.session['search_query'] = query
            redirect('api:nexi')
        else:
            name = request.POST.get("name")
            lastname = request.POST.get("lastname")
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
            distance = query.get('distance')
            travel_time = query.get('travel_time')
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
                'lastname': lastname
            }
            return render(request, 'booking/booking-payment.html', context)
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
    distance = query.get('distance')
    travel_time = query.get('travel_time')
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
        'lastname': lastname
    }
    return render(request, 'booking/booking-payment.html', context)


def nexi(request):
    terms = request.POST.get("terms")
    if terms == 'on':
        terms_ = True
    else:
        terms_ = False
    # print(terms)
    # breakpoint()
    billing_name = request.POST.get("billing_name")
    # breakpoint()
    # print(billing_name)
    billing_lastname = request.POST.get("billing_lastname")
    billing_company = request.POST.get("billing_company")
    billing_address = request.POST.get("billing_address")
    # Query
    query = request.session['search_query']
    # breakpoint()
    # print(query)
    from_short = query.get('from_short')
    from_hidden = query.get('from_hidden')
    to_short = query.get('to_short')
    to_hidden = query.get('to_hidden')
    to_date = query.get('to_date')
    to_time = query.get('to_time')
    car_class = query.get('car_class')
    rate = query.get('rate')
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
    context = {
        'booking_id': booking_id,
        'session_id': session_id,
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
        'billing_name': billing_name,
        'billing_lastname': billing_lastname,
        'billing_company': billing_company,
        'billing_address': billing_address,
        'terms': terms
    }
    # Генерация PDF и сохранение в MEDIA_ROOT
    # str_id = str(session_id)
    # voucher_name = f"voucher_{str_id}.pdf"
    subject = 'Your booking was submitted successfully'
    from_email = settings.DEFAULT_FROM_EMAIL
    to = [email, from_email]
    subject = 'Your booking was submitted successfully'
    from_email = settings.DEFAULT_FROM_EMAIL
    to = [email, from_email]
    # Рендеринг HTML-шаблона1
    html_content = render_to_string('booking/booking-received.html', context)
    # Отправка письма
    send_mail(
        subject=subject,
        message='',  # Текстовое сообщение которые не поддерживают HTML
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=to,
        html_message=html_content,
        fail_silently=False,
    )
    return render(request, 'booking/booking-received.html', context)


def link_callback(uri, rel):
    result = finders.find(uri)
    if result:
        if not isinstance(result, (list, tuple)):
            result = [result]
            result = list(os.path.realpath(path) for path in result)
            path = result[0]
    else:
        sUrl = settings.STATIC_URL
        sRoot = settings.STATIC_ROOT
        mUrl = settings.MEDIA_URL
        mRoot = settings.MEDIA_ROOT
        if uri.startswith(mUrl):
            path = os.path.join(mRoot, uri.replace(mUrl, ""))
        elif uri.startswith(sUrl):
            path = os.path.join(sRoot, uri.replace(sUrl, ""))
        else:
            return uri
        # make sure that file exists
        if not os.path.isfile(path):
            raise RuntimeError(
                'media URI must start with %s or %s' % (sUrl, mUrl))
    return path


def emailtest(request):
    # PDF xhtml2pdf
    # HTML
    context = {}
    html_content = render_to_string("booking/booking-received.html", context)
    text_content = strip_tags(html_content)
    # PDF
    template = get_template("booking/booking-received.html")
    html = template.render(context)
    result = BytesIO()
    pdf = pisa.CreatePDF(BytesIO(html.encode("UTF-8")),
                         dest=result,
                         link_callback=link_callback)
    if pdf.err:
        return HttpResponse('Error occurred while generating PDF', status=500)
    pdf_value = result.getvalue()
    result.close()
    subject = 'TEST PDF'
    from_email = 'support@transferslux.com'
    recepients = 'shooroop87@mail.ru'
    email_message = EmailMultiAlternatives(subject,
                                           text_content,
                                           from_email,
                                           to=[recepients])
    # Attach the PDF file
    email_message.content_subtype = 'html'
    email_message.attach('report.pdf', pdf_value, 'application/pdf')
    email_message.send()
    return render(request, 'index.html')


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
