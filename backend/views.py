# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.http import HttpResponse
from django.shortcuts import render

import json

# Create your views here.

def json_response(data):
    return HttpResponse(json.dumps(data), content_type="application/json")

def query(request):
    text = request.POST.get('text')
    data = {'error': 0, 'msg': 'Input: {0}'.format(text)}
    return json_response(data)

def tips(request):
    data = {'error': 0, 'msg': 'response from backend:tips'}
    return json_response(data)
