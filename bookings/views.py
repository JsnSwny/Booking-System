from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from .models import Booking, Alert, Staff, TableGroup, TableItem, Settings, Takeaway
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
import datetime
from datetime import date
import random
import time
from collections import Counter
from dateutil import parser
from django.core import serializers
import json
import os
import logging
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.utils.html import strip_tags
import csv
from django.contrib.auth import authenticate, login
from .forms import LoginForm
from django.contrib.auth.views import LoginView
import calendar
from collections import OrderedDict
import pandas as pd


def getAjaxRequest(request, id):
    data = {}
    if request.is_ajax():

        # Booking List
        if id == 1:
            date = request.GET.get('date')
            datetime_object = datetime.datetime.strptime(date, '%d/%m/%Y')

            bookings = Booking.objects.filter(
                date=datetime_object, user_id=request.user.id).order_by('time')
            bookings_dict = serializers.serialize('python', bookings)

            alerts = Alert.objects.filter(
                date=datetime_object, user_id=request.user.id)
            alerts_dict = serializers.serialize('python', alerts)

            for i in bookings_dict:
                if TableItem.objects.filter(pk=i['fields']['table']).first() != None:
                    table = TableItem.objects.filter(
                        pk=i['fields']['table']).first().name
                    colour = TableItem.objects.filter(
                        pk=i['fields']['table']).first().group.colour
                    i.update({'table': table})
                    i.update({'colour': colour})
                else:
                    i.update({'table': "None"})

            data['objects'] = bookings_dict
            data['alerts'] = alerts_dict
            current_user = request.user

        # Update Table
        elif id == 2:
            table_id = request.GET.get('table_id')
            id = request.GET.get('id')

            table = TableItem.objects.filter(pk=table_id).first()
            Booking.objects.filter(pk=id).update(table=table)

        # Get Booking
        elif id == 3:
            id = request.GET.get('id')
            booking = Booking.objects.filter(
                id=id, user_id=request.user.id).first()
            people = booking.people
            name = booking.name
            time = booking.time
            arrived = booking.arrived
            cleared = booking.cleared
            booking_type = booking.booking_type

            data = {'people': people, 'name': name, 'time': time,
                    'id': id, 'arrived': arrived, 'cleared': cleared, 'booking_type': booking_type}

        # Add Walk In
        elif id == 4:
            id = request.GET.get('id')
            people = request.GET.get('people')
            booking_type = request.GET.get('booking_type')

            if people == '':
                people = 0

            if int(people) <= TableItem.objects.filter(pk=id)[0].people and int(people) > 0:
                addWalkIn(id, people, request.user.id, booking_type)
            else:
                data = {'valid': 'False'}

        # Get Available Tables
        elif id == 5:
            time = request.GET.get('time')
            date = datetime.datetime.now().date()
            bookings = Booking.objects.filter(
                date=date, user_id=request.user.id)
            tables = TableItem.objects.filter(
                user_id=request.user.id).order_by('group', 'name')
            available = []
            unavailable = []

            for i in tables:
                if i.people > 0:
                    available.append(i)

            for b in bookings:
                p = datetime.datetime.combine(date, b.time)
                t = datetime.datetime.combine(
                    date, datetime.datetime.strptime(time, '%H:%M').time())
                time_dif = (p - t)
                hours = abs(time_dif.total_seconds() / 3600)

                if hours < 3 and hours > -3 and b.cleared == False:
                    if b.table in available:
                        available.remove(b.table)
                        unavailable.append(b.table)

            available_dict = serializers.serialize('python', available)
            unavailable_dict = serializers.serialize('python', unavailable)
            for i in unavailable_dict:
                colour = TableGroup.objects.filter(
                    pk=i['fields']['group']).first().colour
                i.update({'colour': colour})
            for i in available_dict:
                colour = TableGroup.objects.filter(
                    pk=i['fields']['group']).first().colour
                group_name = TableGroup.objects.filter(
                    pk=i['fields']['group']).first().name

                i.update({'colour': colour})
                i.update({'group_name': group_name})

            data['available'] = available_dict
            data['unavailable'] = unavailable_dict
        elif id == 6:
            id = request.GET.get('id')
            Booking.objects.filter(pk=id).update(arrived='True')
        elif id == 7:
            id = request.GET.get('id')
            Booking.objects.filter(pk=id).update(cleared='True')
        elif id == 8:
            id = request.GET.get('id')
            Booking.objects.filter(pk=id).update(arrived='False')
            Booking.objects.filter(pk=id).update(cleared='False')
        elif id == 9:
            id = request.GET.get('id')
            booking = Booking.objects.filter(pk=id).first()
            Booking.objects.filter(pk=id).delete()
            Booking.history.filter(name="Walk In").delete()

        elif id == 10:
            date = request.GET.get('date')
            time = request.GET.get('time')
            name = request.GET.get('name')
            people = request.GET.get('people')
            taker = request.GET.get('taker')
            tel = request.GET.get('tel')
            additional = request.GET.get('additional')
            userid = request.GET.get('userid')
            email = request.GET.get('email')
            booking_type = request.GET.get('booking_type')
            if userid == None:
                userid = request.user.id

            if email != None:
                booking = Booking(initials=taker, name=name, people=people, time=time,
                                  date=date, tel=tel, info=additional, user_id=userid, online=True)
                user = User.objects.get(id=userid)
                restaurant_name = Settings.objects.filter(
                    user=User.objects.get(id=userid)).first().restaurant_name
                html_message = render_to_string('bookings/mail_template.html', {
                                                'restaurant': restaurant_name, 'date': date, 'time': time, 'name': name, 'people': people})
                plain_message = strip_tags(html_message)
                send_mail("Table Reservation", plain_message, "reservetableuk@gmail.com", [
                          email], html_message=html_message)

                full_message = f'Reservation made online at { time } for {people} on {date} under the name of "{name}"'
                send_mail("Table Reservation", full_message,
                          "reservetableuk@gmail.com", [user.usersettings.email])
            else:
                booking = Booking(initials=taker, name=name, people=people,
                                  time=time, date=date, tel=tel, info=additional, user_id=userid, booking_type=booking_type)

            booking.save()
        elif id == 11:
            id = request.GET.get('id')
            booking = Booking.objects.filter(pk=id)
            booking_dict = serializers.serialize('python', booking)
            data['booking'] = booking_dict
        elif id == 12:
            date = request.GET.get('date')
            time = request.GET.get('time')
            name = request.GET.get('name')
            people = request.GET.get('people')
            taker = request.GET.get('taker')
            tel = request.GET.get('tel')
            additional = request.GET.get('additional')
            booking_type = request.GET.get('booking_type')
            id = request.GET.get('id')

            Booking.objects.filter(pk=id).update(
                initials=taker, name=name, people=people, time=time, date=date, tel=tel, info=additional, booking_type=booking_type)
            for e in Booking.objects.filter(pk=id):
                e.save()

        elif id == 13:
            date = request.GET.get('date')
            message = request.GET.get('message')
            alert = Alert(date=date, message=message, user_id=request.user.id)
            alert.save()

        elif id == 14:
            id = request.GET.get('id')
            alert = Alert.objects.filter(pk=id)
            data = {'message': alert[0].message,
                    'date': alert[0].date, 'id': id}

        elif id == 15:
            date = request.GET.get('date')
            message = request.GET.get('message')
            id = request.GET.get('id')
            Alert.objects.filter(pk=id).update(date=date, message=message)
        elif id == 16:
            id = request.GET.get('id')
            Alert.objects.filter(pk=id).delete()
        elif id == 17:
            total_people = 0
            total_people_close = 0
            total_people_now = 0
            date = request.GET.get('date')
            time = request.GET.get('time')
            date = date.split("/")
            date = f'{date[2]}-{date[1]}-{date[0]}'
            date = datetime.datetime.strptime(date, '%Y-%m-%d')
            bookings = Booking.objects.filter(
                date=date, user_id=request.user.id)
            for i in bookings:
                p = datetime.datetime.combine(date, i.time)
                t = datetime.datetime.combine(
                    date, datetime.datetime.strptime(time, '%H:%M').time())
                time_dif = (p - t)
                hours = abs(time_dif.total_seconds() / 3600)

                if hours < 3 and hours > -3:
                    total_people += i.people
                if hours <= 0.5 and hours >= -0.5:
                    total_people_close += i.people
                if hours == 0:
                    total_people_now += i.people

            data['total_people'] = total_people
            data['total_people_now'] = total_people_now
        elif id == 18:
            dates = []
            people = []
            bookings = Booking.objects.filter(user_id=request.user.id)
            for i in bookings:
                if i.date.strftime('%d/%m/%Y') not in dates:
                    total_people = 0
                    total_people_bookings = Booking.objects.filter(
                        date=i.date, user_id=request.user.id)
                    for i in total_people_bookings:
                        total_people += i.people
                    dates.append(i.date.strftime('%d/%m/%Y'))
                    people.append(total_people)
            data['dates'] = dates
            data['people'] = people
        elif id == 19:
            tables = Table.objects.filter(booking=None).order_by('table')
            tables_dict = serializers.serialize('python', tables)
            data['tables'] = tables_dict
        elif id == 20:
            table_id = request.GET.get('table_id')
            people = request.GET.get('people')
            table = TableItem.objects.filter(pk=table_id)

            table.update(people=people)
            Booking.objects.filter(table=table.first()).update(table=None)

        elif id == 21:
            id = request.GET.get('id')
            assign = request.GET.get('assign')
            Booking.objects.filter(pk=id).update(assign=assign)
        elif id == 22:
            times_people = []
            date = request.GET.get('date')
            times = request.GET.getlist('times[]')

            date = date.split("/")
            date = f'{date[2]}-{date[1]}-{date[0]}'
            date = datetime.datetime.strptime(date, '%Y-%m-%d')
            bookings = Booking.objects.filter(
                date=date, user_id=request.user.id)
            for time in times:
                total_people = 0
                for i in bookings:
                    p = datetime.datetime.combine(date, i.time)
                    t = datetime.datetime.combine(
                        date, datetime.datetime.strptime(time, '%H:%M').time())
                    time_dif = (p - t)
                    hours = abs(time_dif.total_seconds() / 3600)

                    if hours < 3 and hours > -3:
                        total_people += i.people
                times_people.append(total_people)
            data['times_people'] = times_people
        elif id == 23:
            bookings = Booking.objects.filter(date=datetime.datetime.now(
            ), time__gte=datetime.datetime.now().time()).order_by('-people')
            for i in bookings:

                table = Table.objects.filter(booking=i)
                for a in table:
                    a.delete()
        elif id == 24:
            total_walkins = len(Booking.objects.filter(walk_in=True))
            total_online = len(Booking.objects.filter(online=True))
            total_phone = len(Booking.objects.filter(
                walk_in=False, online=False))

            # bookings = Booking.objects.filter(date=datetime.datetime.now())
            # for i in bookings:
            #     if i.name == "Walk In":
            #         no_of_walk_in += 1
            #     else:
            #         no_of_booking += 1
            data['total_walkin'] = total_walkins
            data['total_online'] = total_online
            data['total_phone'] = total_phone
        elif id == 25:
            name = request.GET.get('name')
            booking = request.GET.get('booking')
            staff = Staff(name=name, booking=booking, user_id=request.user.id)
            staff.save()
        elif id == 26:
            Staff.objects.filter(id=request.GET.get('id')).delete()
        elif id == 27:
            name = request.GET.get('name')
            colour = request.GET.get('colour')
            group = TableGroup(name=name, colour=colour,
                               user_id=request.user.id)
            group.save()
        elif id == 28:
            name = request.GET.get('name')
            group = TableGroup.objects.filter(name=request.GET.get(
                'group'), user_id=request.user.id).first()
            table = TableItem(name=name, group=group,
                              people=0, user_id=request.user.id)
            table.save()
        elif id == 29:
            name = request.GET.get('name')
            id = request.GET.get('id')
            TableItem.objects.filter(pk=id).update(name=name)
        elif id == 30:
            id = request.GET.get('id')
            TableItem.objects.filter(pk=id).delete()

        elif id == 31:
            name = request.GET.get('name')
            colour = request.GET.get('colour')
            id = request.GET.get('id')
            TableGroup.objects.filter(pk=id).update(name=name, colour=colour)
        elif id == 32:
            id = request.GET.get('id')
            TableGroup.objects.filter(pk=id).delete()
        elif id == 33:
            groups = TableGroup.objects.filter(
                user_id=request.user.id).order_by('pk')
            group_dict = serializers.serialize('python', groups)
            for idx, item in enumerate(group_dict):
                tables = TableItem.objects.filter(
                    group=groups[idx]).order_by('pk')
                tables = serializers.serialize('python', tables)
                item.update({'tables': tables})
            data['groups'] = group_dict

        elif id == 34:
            table_groups = {}
            table_group = TableGroup.objects.filter(
                user_id=request.user.id).order_by('pk')
            for i in table_group:
                table_groups[i.name] = [i.pk]

            for i in TableItem.objects.filter(user_id=request.user.id).order_by('name'):
                table_groups[i.group.name].append(
                    [i.name, i.pk, i.people, i.group.colour])
            data['tables'] = table_groups

        elif id == 35:
            staff = []
            for i in Staff.objects.filter(user_id=request.user.id).order_by('name'):
                staff.append([i.name, i.pk])
            data['staff'] = staff

        elif id == 36:
            name = request.GET.get('name')
            email = request.GET.get('email')
            phone = request.GET.get('phone')
            address = request.GET.get('address')
            message = request.GET.get('message')

            full_message = f'From: {name} \nEmail: {email}\nPhone: {phone}\nAddress: {address}\nMessage: {message}'
            send_mail("Booking System Contact!", full_message,
                      "jsnswny@gmail.com", ['jsnswny@gmail.com'])
        elif id == 37:
            old_password = request.GET.get('old_password')
            new_password = request.GET.get('new_password')
            if request.user.check_password(old_password):
                request.user.set_password(new_password)
                request.user.save()

        elif id == 38:
            user = request.GET.get('user')
            date = request.GET.get('date')
            people = request.GET.get('people')

            datetime_object = datetime.datetime.strptime(date, '%d/%m/%Y')

            id = User.objects.get(username=user).pk
            bookings = Booking.objects.filter(user_id=id, date=datetime_object)

            times = []
            obj = {}
            hour_obj = {}

            bookings = Booking.objects.filter(user_id=id, date=datetime_object)
            for b in bookings:
                obj.setdefault(str(b.time)[0:5], 0)
                obj[str(b.time)[0:5]] = obj[str(b.time)[0:5]] + b.people

                hour_obj.setdefault(str(b.time)[0:2], 0)
                hour_obj[str(b.time)[0:2]] = hour_obj[str(
                    b.time)[0:2]] + b.people

            data['hour'] = hour_obj
            data['time'] = obj

        elif id == 39:
            monday = request.GET.get('monday')
            tuesday = request.GET.get('tuesday')
            wednesday = request.GET.get('wednesday')
            thursday = request.GET.get('thursday')
            friday = request.GET.get('friday')
            saturday = request.GET.get('saturday')
            sunday = request.GET.get('sunday')
            restaurant_name = request.GET.get('restaurant_name')
            max_at_time = request.GET.get('max-at-time')
            max_at_hour = request.GET.get('max-at-hour')
            email = request.GET.get('email')
            phone = request.GET.get('phone')

            if len(Settings.objects.filter(user=request.user)) > 0:
                Settings.objects.filter(user=request.user).update(
                    monday=monday, tuesday=tuesday, wednesday=wednesday, thursday=thursday,
                    friday=friday, saturday=saturday, sunday=sunday,
                    restaurant_name=restaurant_name, max_at_time=max_at_time, max_at_hour=max_at_hour,
                    phone=phone, email=email)
            else:
                setting = Settings(monday=monday, tuesday=tuesday, wednesday=wednesday, thursday=thursday,
                                   friday=friday, saturday=saturday, sunday=sunday, restaurant_name=restaurant_name, user=request.user,
                                   max_at_time=max_at_time, max_at_hour=max_at_hour, phone=phone, email=email)
                setting.save()
        elif id == 40:
            name = request.GET.get('name')
            people = request.GET.get('people')
            address = request.GET.get('address')
            telephone = request.GET.get('telephone')
            info = request.GET.get('info')
            takeaway = Takeaway(name=name, people=people, address=address,
                                tel=telephone, info=info, date=datetime.datetime.now(), user_id=request.user.id)
            takeaway.save()
        elif id == 41:
            date = request.GET.get('date')
            datetime_object = datetime.datetime.strptime(date, '%d/%m/%Y')

            takeaways = Takeaway.objects.filter(
                date=datetime_object, user_id=request.user.id).order_by('id')
            takeaways_dict = serializers.serialize('python', takeaways)

            data['takeaways'] = takeaways_dict
            current_user = request.user
        elif id == 42:
            id = request.GET.get('id')
            Takeaway.objects.filter(pk=id).delete()

    return JsonResponse(data)


# def logincheck(request):

#     if request.user.is_authenticated:
#         return HttpResponseRedirect('/bookings')

#     if request.method == 'POST':
#         form = LoginForm(request.POST)
#         if form.is_valid():
#             data = form.cleaned_data
#             username = data['username']
#             password = data['password']
#             user = authenticate(request, username=username, password=password)
#             if user is not None:
#                 login(request, user)
#                 return HttpResponseRedirect('/bookings')
#     else:
#         form = LoginForm()
#     return render(request, 'bookings/login.html', {'form': form})

def download(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="bookings.csv"'

    writer = csv.writer(response)

    writer.writerow(['ID', 'Date', 'Time', 'Name',
                     'People', 'Contact', 'Info', 'Taker'])
    for i in Booking.objects.filter(user_id=request.user.id).order_by('-date', '-time'):
        i.time = str(i.time)[0:6]
        i.tel = "=\"" + str(i.tel) + "\""
        writer.writerow([i.id, i.date, i.time, i.name,
                         i.people, i.tel, i.info, i.initials])

    return response


def addWalkIn(table, people, userid, booking_type):
    table = TableItem.objects.filter(pk=table).first()
    booking = Booking(name='Walk In', arrived='True', people=people, time=datetime.datetime.now(
    ).time(), date=datetime.datetime.now(), table=table, user_id=userid, walk_in=True, booking_type=booking_type)
    booking.save()
    Booking.history.filter(name="Walk In").delete()


def book(request, username):
    u = User.objects.get(username=username).pk
    return render(request, 'bookings/booking.html', {'username': username, 'userid': u, 'settings': Settings.objects.filter(user=User.objects.get(username=username)).first()})


def available_tables():

    bookings = Booking.objects.filter(date=datetime.datetime.now())
    tables = Table.objects.filter(booking=None)
    available = []
    unavailable = []

    for i in tables:
        if i.table > 0:
            if i.people > 0:
                available.append((i.table, i.people))

    for b in bookings:
        b_tables = Table.objects.filter(booking=b)
        p = datetime.datetime.combine(datetime.datetime.now(), b.time)
        t = datetime.datetime.combine(
            datetime.datetime.now(), datetime.datetime.now().time())
        time_dif = (p - t)
        hours = abs(time_dif.total_seconds() / 3600)
        if hours < 3 and hours > -3:
            for i in b_tables:
                unavailable.append((i.table, Table.objects.filter(
                    booking=None, table=i.table)[0].people))
                if (i.table, Table.objects.filter(booking=None, table=i.table)[0].people) in available:
                    available.remove((i.table, Table.objects.filter(
                        booking=None, table=i.table)[0].people))
    return [unavailable, available]


def tablelayout(request):
    tables = TableGroup.objects.filter(user_id=request.user.id).order_by('pk')
    return render(request, 'bookings/settings_table_layout.html', {'tables': tables})


def changepassword(request):
    return render(request, 'bookings/changepassword.html')


def stats(request):
    first_date = Booking.objects.all().first().date
    calendar.monthrange(date.today().year, date.today().month)

    month = date.today().month
    year = date.today().year
    _, num_days = calendar.monthrange(year, month)

    week_start = date.today() - datetime.timedelta(days=date.today().weekday())
    week_end = week_start + datetime.timedelta(days=6)

    month_list = pd.date_range((first_date - datetime.timedelta(days=29)).strftime("%Y-%m-%d"), date.today().strftime("%Y-%m-%d"),
                               freq='MS').strftime("%Y-%b").tolist()

    total_people = sum([x['people']
                        for x in Booking.objects.all().values('people')])

    month_bookings = []
    for i in month_list:
        month_date = datetime.datetime.strptime(i, '%Y-%b').date()
        _, num_days_month = calendar.monthrange(
            month_date.year, month_date.month)

        month_bookings.append(get_booking_stats(month_date, date(
            month_date.year, month_date.month, num_days_month), request.user.id)['total_people'])
    return render(request, 'bookings/stats.html',
                  {'year': get_booking_stats(date(year, 1, 1), date(year, 12, 31), request.user.id),
                   'month': get_booking_stats(date(year, month, 1), date(year, month, num_days), request.user.id),
                   'week': get_booking_stats(week_start, week_end, request.user.id),
                   'name': request.user, 'first_date': first_date,
                   'month_list': month_list, 'month_bookings': month_bookings,
                   'week_num': datetime.date(date.today().year, date.today().month, date.today().day).isocalendar()[1],
                   'year_num': date.today().year, 'month_num': date.today().strftime("%B"),
                   'total_bookings': f'{len(Booking.objects.all()):,}',
                   'total_people': f'{total_people:,}',
                   'average_people': "{0:.2f}".format(total_people/len(Booking.objects.all()))})


def get_booking_stats(date_from, date_to, user_id):

    # date_from_obj = datetime.datetime.strptime(date_from, '%Y-%m-%d').date()
    # date_to_obj = datetime.datetime.strptime(date_to, '%Y-%m-%d').date()
    total_people = 0

    total_walk_p = 0
    total_book_p = 0
    total_online_p = 0

    total_walk_t = 0
    total_book_t = 0
    total_online_t = 0

    for i in Booking.objects.filter(user_id=user_id):
        if i.date >= date_from and i.date <= date_to:
            total_people += i.people
            if i.walk_in == True:
                total_walk_p += i.people
                total_walk_t += 1
            elif i.online == True:
                total_online_p += i.people
                total_online_t += 1
            else:
                total_book_p += i.people
                total_book_t += 1

    return {'total_walk_p': total_walk_p, 'total_online_p': total_online_p, 'total_book_p': total_book_p,
            'total_walk_t': total_walk_t, 'total_online_t': total_online_t, 'total_book_t': total_book_t,
            'total_people': total_people}


def settings(request):
    return render(request, 'bookings/settings.html', {'settings': Settings.objects.filter(user=request.user).first()})


def stafflist(request):
    staff = Staff.objects.filter(user_id=request.user.id)
    return render(request, 'bookings/settings_staff_list.html', {'staff': staff})


def bookings(request):
    staff = Staff.objects.filter(user_id=request.user.id)
    return render(request, 'bookings/booking_list.html', {
        'staff': staff,
        'groups': TableGroup.objects.all(),
        'today_people': sum([x['people'] for x in Booking.objects.filter(user_id=request.user.id, date=datetime.datetime.now()).values('people')]),
        'today_tables': len(Booking.objects.filter(user_id=request.user.id, date=datetime.datetime.now())),
        'today_takeaways': len(Takeaway.objects.filter(date=datetime.datetime.now(), user_id=request.user.id)),
        'today_meals': len(Booking.objects.filter(date=datetime.datetime.now(), user_id=request.user.id, booking_type="M")),
        'today_drinks': len(Booking.objects.filter(date=datetime.datetime.now(), user_id=request.user.id, booking_type="D"))
    })


def history(request):
    if request.is_ajax():
        data = {}
        id = request.GET.get('id')
        history_list = Booking.history.filter(id=id, user_id=request.user.id)
        paginator = Paginator(history_list, 25)  # Show 25 contacts per page
        page = request.GET.get('page')
        history = paginator.get_page(page)
        history = serializers.serialize('python', history)
        data['history'] = history
        return JsonResponse(data)
    else:
        history_list = Booking.history.all().filter(user_id=request.user.id)
        paginator = Paginator(history_list, 25)  # Show 25 contacts per page
        page = request.GET.get('page')
        history = paginator.get_page(page)
        return render(request, 'bookings/history.html', {'history': history})


def create(request):
    staff = Staff.objects.filter(booking=True, user_id=request.user.id)
    return render(request, 'bookings/createbooking.html', {'staff': staff})


def total_people_on_table(instance):
    tot = 0
    booking_tables = Table.objects.filter(booking=instance)
    for i in booking_tables:
        num_people = (Table.objects.filter(booking=None, table=i.table))[0]
        tot += num_people.people
    return (instance.people - tot)
