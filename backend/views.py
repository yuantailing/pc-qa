# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.http import HttpResponse
from django.shortcuts import render

import json
import localqa
import os

# Create your views here.

DATA_ROOT = 'data'

with open(os.path.join(DATA_ROOT, 'series.json')) as f:
    series = json.load(f)

api = localqa.api.Api('config')

def json_response(data):
    return HttpResponse(json.dumps(data), content_type="application/json")

def query(request):
    text = request.POST.get('text')
    v = []
    for s in series:
        for p in s['products']:
            if len(v) < 5:
                for t in p['内存容量']:
                    if -1 != t.find('8GB'):
                        v.append(p)
                        break
    data = {'error': 0,
            'msg': {
                'constraints': ['内存：8GB', '外观：轻薄'],
                'products': v,
            },
        }
    return json_response(data)

def tips(request):
    data = {'error': 0, 'msg': 'response from backend:tips'}
    return json_response(data)
