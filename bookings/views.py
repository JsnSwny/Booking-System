from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from .models import Booking, Alert, Staff, TableGroup, TableItem
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
import datetime
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

from django.core.mail import send_mail

from django.conf import settings



def getAjaxRequest(request, id):
    data = {}
    if request.is_ajax():
        

        # Booking List
        if id == 1:  
            date = request.GET.get('date')
            datetime_object = datetime.datetime.strptime(date, '%d/%m/%Y')

            bookings = Booking.objects.filter(date=datetime_object, user_id=request.user.id).order_by('time')
            bookings_dict = serializers.serialize('python', bookings)

            alerts = Alert.objects.filter(date=datetime_object, user_id=request.user.id)
            alerts_dict = serializers.serialize('python', alerts)

            for i in bookings_dict:
                if TableItem.objects.filter(pk = i['fields']['table']).first() != None:
                    table = TableItem.objects.filter(pk = i['fields']['table']).first().name
                    colour = TableItem.objects.filter(pk = i['fields']['table']).first().group.colour
                    i.update({'table':table})
                    i.update({'colour':colour})
                else:
                    i.update({'table':"None"})

            data['objects'] = bookings_dict
            data['alerts'] = alerts_dict
            current_user = request.user



        # Update Table
        elif id == 2:
            table_id = request.GET.get('table_id')
            id = request.GET.get('id')
            
            table = TableItem.objects.filter(pk=table_id).first()
            Booking.objects.filter(pk=id).update(table = table)

        # Get Booking
        elif id == 3:
            id = request.GET.get('id')
            booking = Booking.objects.filter(id=id, user_id=request.user.id).first() 
            people = booking.people
            name = booking.name
            time = booking.time
            arrived = booking.arrived
            cleared = booking.cleared

            data = {'people': people, 'name': name, 'time': time, 'id': id, 'arrived': arrived, 'cleared': cleared}

        # Add Walk In
        elif id == 4:
            id = request.GET.get('id')
            people = request.GET.get('people')

            if people == '':
                people = 0

            if int(people) <= TableItem.objects.filter(pk=id)[0].people and int(people) > 0:
                addWalkIn(id, people, request.user.id)     
            else:
                data = {'valid': 'False'}
            

        # Get Available Tables
        elif id == 5:
            time = request.GET.get('time')
            date = datetime.datetime.now().date()
            bookings = Booking.objects.filter(date=date, user_id=request.user.id)
            tables = TableItem.objects.filter(user_id=request.user.id).order_by('group', 'pk')
            available = []
            unavailable = []

            for i in tables:
                if i.people > 0:
                    available.append(i)

            for b in bookings:
                p = datetime.datetime.combine(date, b.time)
                t = datetime.datetime.combine(date, datetime.datetime.strptime(time, '%H:%M').time())
                time_dif = (p - t)
                hours = abs(time_dif.total_seconds() / 3600)

                if hours < 3 and hours > -3 and b.cleared == False:
                    if b.table in available:
                        available.remove(b.table)
                        unavailable.append(b.table)
            

            available_dict = serializers.serialize('python', available)
            unavailable_dict = serializers.serialize('python', unavailable)
            for i in unavailable_dict:
                colour = TableGroup.objects.filter(pk=i['fields']['group']).first().colour
                i.update({'colour':colour})
            for i in available_dict:
                colour = TableGroup.objects.filter(pk=i['fields']['group']).first().colour
                group_name = TableGroup.objects.filter(pk=i['fields']['group']).first().name

                i.update({'colour':colour})
                i.update({'group_name':group_name})

            data['available'] = available_dict
            data['unavailable'] = unavailable_dict
        elif id == 6:
            id = request.GET.get('id')
            Booking.objects.filter(pk=id).update(arrived = 'True')
        elif id == 7:
            id = request.GET.get('id')
            Booking.objects.filter(pk=id).update(cleared = 'True')
        elif id == 8:
            id = request.GET.get('id')
            Booking.objects.filter(pk=id).update(arrived = 'False')
            Booking.objects.filter(pk=id).update(cleared = 'False')
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
            booking = Booking(initials = taker, name = name, people = people, time = time, date = date, tel=tel, info=additional, user_id=request.user.id)
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
            id = request.GET.get('id')

            Booking.objects.filter(pk=id).update(initials = taker, name = name, people = people, time = time, date = date, tel=tel, info=additional)
            for e in Booking.objects.filter(pk=id):
                e.save()

        elif id == 13:
            date = request.GET.get('date')
            message = request.GET.get('message')
            alert = Alert(date = date, message = message, user_id=request.user.id)
            alert.save()

        elif id == 14:
            id = request.GET.get('id')
            alert = Alert.objects.filter(pk=id)
            data = {'message': alert[0].message, 'date': alert[0].date, 'id': id}

        elif id == 15:
            date = request.GET.get('date')
            message = request.GET.get('message')
            id = request.GET.get('id')
            Alert.objects.filter(pk=id).update(date = date, message = message)
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
            bookings = Booking.objects.filter(date=date, user_id=request.user.id)
            for i in bookings:
                p = datetime.datetime.combine(date, i.time)
                t = datetime.datetime.combine(date, datetime.datetime.strptime(time, '%H:%M').time())
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
            bookings = Booking.objects.all()
            for i in bookings:
                if i.date.strftime('%d/%m/%Y') not in dates:
                    total_people = 0
                    total_people_bookings = Booking.objects.filter(date=i.date)
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

            table.update(people = people)
            Booking.objects.filter(table = table.first()).update(table = None)

        elif id == 21:
            id = request.GET.get('id')
            assign = request.GET.get('assign')
            Booking.objects.filter(pk=id).update(assign = assign)
        elif id == 22:
            times_people = []
            date = request.GET.get('date')
            times = request.GET.getlist('times[]')

            date = date.split("/")
            date = f'{date[2]}-{date[1]}-{date[0]}'
            date = datetime.datetime.strptime(date, '%Y-%m-%d')
            bookings = Booking.objects.filter(date=date, user_id=request.user.id)
            for time in times:
                total_people = 0
                for i in bookings:
                    p = datetime.datetime.combine(date, i.time)
                    t = datetime.datetime.combine(date, datetime.datetime.strptime(time, '%H:%M').time())
                    time_dif = (p - t)
                    hours = abs(time_dif.total_seconds() / 3600)

                    if hours < 3 and hours > -3:
                        total_people += i.people
                times_people.append(total_people)
            data['times_people'] = times_people
        elif id == 23:
            bookings = Booking.objects.filter(date=datetime.datetime.now(), time__gte=datetime.datetime.now().time()).order_by('-people')
            for i in bookings:

                table = Table.objects.filter(booking=i)
                for a in table:
                    a.delete()
        elif id == 24:
            span = request.GET.get('span')
            no_of_walk_in = 1
            no_of_booking = 1
            if span == "today":
                bookings = Booking.objects.filter(date=datetime.datetime.now())
                for i in bookings:
                    if i.name == "Walk In":
                        no_of_walk_in += 1
                    else:
                        no_of_booking += 1
            data['walk_in'] = no_of_walk_in
            data['booking'] = no_of_booking
        elif id == 25:
            name = request.GET.get('name')
            booking = request.GET.get('booking')
            staff = Staff(name = name, booking = booking, user_id=request.user.id)
            staff.save()
        elif id == 26:
            Staff.objects.filter(id = request.GET.get('id')).delete()
        elif id == 27:
            name = request.GET.get('name')
            colour = request.GET.get('colour')
            group = TableGroup(name = name, colour = colour, user_id=request.user.id)
            group.save()
        elif id == 28:
            name = request.GET.get('name')
            group = TableGroup.objects.filter(name = request.GET.get('group'), user_id=request.user.id).first()
            table = TableItem(name = name, group = group, people = 0, user_id=request.user.id)
            table.save()
        elif id == 29:
            name = request.GET.get('name')
            id = request.GET.get('id')
            TableItem.objects.filter(pk = id).update(name = name)
        elif id == 30:
            id = request.GET.get('id')
            TableItem.objects.filter(pk = id).delete()

        elif id == 31:
            name = request.GET.get('name')
            colour = request.GET.get('colour')
            id = request.GET.get('id')
            TableGroup.objects.filter(pk = id).update(name = name, colour = colour)
        elif id == 32:
            id = request.GET.get('id')
            TableGroup.objects.filter(pk = id).delete()
        elif id == 33:
            groups = TableGroup.objects.filter(user_id=request.user.id).order_by('pk')
            group_dict = serializers.serialize('python', groups)
            for idx, item in enumerate(group_dict):
                tables = TableItem.objects.filter(group=groups[idx]).order_by('pk')
                tables = serializers.serialize('python', tables)
                item.update({'tables': tables})
            data['groups'] = group_dict

        elif id == 34:
            table_groups = {}
            table_group = TableGroup.objects.filter(user_id=request.user.id).order_by('pk')
            for i in table_group:
                table_groups[i.name] = [i.pk]

            for i in TableItem.objects.filter(user_id=request.user.id).order_by('pk'):
                table_groups[i.group.name].append([i.name, i.pk, i.people, i.group.colour])

            print(table_groups)
            data['tables'] = table_groups

        elif id == 35:
            staff = []
            for i in Staff.objects.filter(user_id=request.user.id).order_by('name'):
                staff.append(i.name)
            data['staff'] = staff

        elif id == 36:
            name = request.GET.get('name')
            email = request.GET.get('email')
            phone = request.GET.get('phone')
            address = request.GET.get('address')
            message = request.GET.get('message')

            full_message = f'From: {name} \nEmail: {email}\nPhone: {phone}\nAddress: {address}\nMessage: {message}'
            send_mail("Booking System Contact!", full_message, "jsnswny@gmail.com", ['jsnswny@gmail.com'])
    return JsonResponse(data)

def addWalkIn(table, people, userid):
    table = TableItem.objects.filter(pk=table).first()
    booking = Booking(name = 'Walk In', arrived = 'True', people = people, time = datetime.datetime.now().time(), date = datetime.datetime.now(), table = table, user_id=userid)
    booking.save()
    Booking.history.filter(name="Walk In").delete()

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
        t = datetime.datetime.combine(datetime.datetime.now(), datetime.datetime.now().time())
        time_dif = (p - t)
        hours = abs(time_dif.total_seconds() / 3600)
        if hours < 3 and hours > -3:
            for i in b_tables:
                unavailable.append((i.table, Table.objects.filter(booking=None, table=i.table)[0].people))
                if (i.table, Table.objects.filter(booking=None, table=i.table)[0].people) in available:
                    available.remove( (i.table, Table.objects.filter(booking=None, table=i.table)[0].people) )
    return [unavailable, available]

def tablelayout(request):
    tables = TableGroup.objects.filter(user_id=request.user.id).order_by('pk')
    return render(request, 'bookings/settings_table_layout.html', {'tables': tables})

def stafflist(request):
    staff = Staff.objects.filter(user_id=request.user.id)
    return render(request, 'bookings/settings_staff_list.html', {'staff': staff})

def bookings(request):
    staff = Staff.objects.filter(user_id=request.user.id)
    return render(request, 'bookings/booking_list.html', {'staff': staff, 'groups': TableGroup.objects.all()})

def history(request):
    if request.is_ajax():
        data = {}
        id = request.GET.get('id')
        history_list = Booking.history.filter(id=id, user_id=request.user.id)
        paginator = Paginator(history_list, 25) # Show 25 contacts per page
        page = request.GET.get('page')
        history = paginator.get_page(page)
        history = serializers.serialize('python', history)   
        data['history'] = history
        return JsonResponse(data)
    else:
        history_list = Booking.history.all().filter(user_id=request.user.id)
        paginator = Paginator(history_list, 25) # Show 25 contacts per page
        page = request.GET.get('page')
        history = paginator.get_page(page)
        return render(request, 'bookings/history.html', {'history': history})

def create(request):
    staff = Staff.objects.filter(booking = True, user_id=request.user.id)
    return render(request, 'bookings/createbooking.html', {'staff': staff})

def total_people_on_table(instance):
    tot = 0
    booking_tables = Table.objects.filter(booking=instance)
    for i in booking_tables:
        num_people = (Table.objects.filter(booking=None, table=i.table))[0]
        tot += num_people.people
    return (instance.people - tot)