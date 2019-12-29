from django import forms
from .models import Alert

class BookingForm(forms.Form):
    time = forms.TimeField()
    name = forms.CharField(max_length = 100)
    people = forms.IntegerField()
    info = forms.CharField(widget=forms.Textarea(attrs={"rows":2, "cols":40}), required=False)
    date = forms.DateField(widget=forms.DateInput(format='%d/%m/%Y'),
        input_formats=('%d/%m/%Y', ))
    tel = forms.CharField(max_length=12, min_length=10, required=False)
    initials = forms.CharField(max_length = 20)

    def __init__(self, *args, **kwargs):
        super(BookingForm, self).__init__(*args, **kwargs)
        self.fields['time'].widget.attrs['placeholder'] = 'e.g "17:00"'
        self.fields['time'].widget.attrs['autofocus'] = 'autofocus'
        self.fields['name'].widget.attrs['placeholder'] = 'e.g "Smith"'
        self.fields['people'].widget.attrs['placeholder'] = 'e.g "6"'
        self.fields['date'].widget.attrs['placeholder'] = 'e.g "21/05/2019"'
        self.fields['tel'].widget.attrs['placeholder'] = 'e.g "01467 123456"'



class AlertForm(forms.Form):
    date = forms.DateField(widget=forms.DateInput(format='%d/%m/%Y'),
        input_formats=('%d/%m/%Y', ))
    message = forms.CharField(widget=forms.Textarea(attrs={"rows":2, "cols":40}))

class LoginForm(forms.Form):
    username = forms.CharField(max_length = 100)
    password = forms.CharField(max_length = 100)