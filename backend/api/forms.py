from django import forms


class SearchForm(forms.Form):
    from_short = forms.CharField(required=True)
    from_hidden = forms.CharField(required=True)
    to_short = forms.CharField(required=True)
    to_hidden = forms.CharField(required=True)
    to_date = forms.CharField()
    to_time = forms.CharField()


class VehicleForm(forms.Form):
    car_class = forms.CharField()
    rate = forms.CharField()


class ExtrasForm(forms.Form):
    flight = forms.CharField(required=False)
    child_seat = forms.CharField(required=False)
    booster_seat = forms.CharField(required=False)
    flowers = forms.CharField(required=False)
    notes_extra = forms.CharField(required=False)


class DetailsForm(forms.Form):
    name = forms.CharField()
    lastname = forms.CharField()
    email = forms.EmailField(
        error_messages={'invalid':
                        'Пожалуйста, введите корректный email адрес.'})
    phone = forms.CharField()
    passengers = forms.CharField()
    luggage = forms.CharField(required=False)
    notes_details = forms.CharField(required=False)


class PaymentForm(forms.Form):
    terms = forms.BooleanField(required=False)
    billing_name = forms.CharField(required=False)
    billing_lastname = forms.CharField(required=False)
    billing_company = forms.CharField(required=False)
    billing_address = forms.CharField(required=False)
