# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.http import HttpResponse
from django.shortcuts import render

import copy
import json
import localqa
import os
import random
import re
from .utils import perfs, props

# Create your views here.

DATA_ROOT = 'data'

with open(os.path.join(DATA_ROOT, 'series.json')) as f:
    series = json.load(f)

api = localqa.api.Api('config')

def friendly_display(obj):
    print(json.dumps(obj, ensure_ascii=False, indent=None, sort_keys=True))

def random_nlg(act_type, kw):
    all = api.nlg(act_type, kw)['msg']
    assert(0 < len(all))
    return random.sample(all, 1)[0]['output']


def json_response(data):
    return HttpResponse(json.dumps(data), content_type="application/json")

def query(request):
    if request.POST.get('status'):
        status = json.loads(request.POST.get('status'))
    else:
        status = {
                'brand': {'in': None, 'not': ['others']},
                'cpu': {'gte': 1.5, 'lte': None},
                'memory': {'gte': 4, 'lte': None},
                'disk': {'gte': 480, 'lte': None},
                'gpu': {'gte': 4, 'lte': None},
                'screen': {'gte': None, 'lte': None},
                'weight': {'gte': None, 'lte': None},
                'market_date': {'gte': None, 'lte': None},
                'price': {'gte': None, 'lte': 8000},
                'seller': {'gte': 10, 'lte': None},
                'price_pos': 0.5,
                }
    def check_between(product, func, rng):
        if rng['gte'] is not None or rng['lte'] is not None:
            prop = func(product)
            if rng['gte'] is not None and (prop is None or prop < rng['gte']): return False
            if rng['lte'] is not None and (prop is None or prop > rng['lte']): return False
        return True
    def search_once(status):
        all = []
        for s in series:
            for p in s['products']:
                if props.is_ill(p): continue
                if status['brand']['in'] is not None and props.brand(p) not in status['brand']['in']: continue
                if props.brand(p) in status['brand']['not']: continue
                if not check_between(p, props.cpu_freq, status['cpu']): continue
                if not check_between(p, props.memory_size, status['memory']): continue
                if not check_between(p, props.disk_size, status['disk']): continue
                if not check_between(p, props.gpu_rank, status['gpu']): continue
                if not check_between(p, props.screen_size, status['screen']): continue
                if not check_between(p, props.weight, status['weight']): continue
                if not check_between(p, props.market_date, status['market_date']): continue
                if not check_between(p, props.price, status['price']): continue
                if not check_between(p, props.seller_num, status['seller']): continue
                all.append(p)
        return all
    text = request.POST.get('text')
    msg = '无模板匹配'
    result = api.nlu(text)
    friendly_display(result)
    assert(result['error'] == 0)
    patternlist = result['msg']['patternlist']
    if 0 != len(patternlist):
        patternlist.sort(key=lambda d: (-d['_level'], -d['_matched_length']))
        pattern = patternlist[0]
        old_status = copy.deepcopy(status)
        act = pattern['_act_type']
        msg = '无逻辑匹配 _act_type={0}'.format(act)
        if act == 'price_dec':
            status['price']['lte'] -= 1000
            if status['price']['gte'] is not None: status['price']['gte'] = min(status['price']['gte'], status['price']['lte'] - 1000)
            if len(search_once(status)) < 1:
                status = old_status
                msg = random_nlg('price_dec_failed', {})
            else:
                msg = random_nlg('price_dec', {})
        elif act == 'brand_no':
            bd = pattern['brand'][0]
            regular_bd = pattern['_regular']['brand'][0]
            if status['brand']['in'] is not None and regular_bd in status['brand']['in']:
                status['brand']['in'].remove(regular_bd)
            if status['brand']['in'] is not None and 0 == len(status['brand']['in']):
                status['brand']['in'] = None
            if regular_bd not in status['brand']['not']:
                status['brand']['not'].append(regular_bd)
            msg = random_nlg('brand_no', {'brand': bd})
        elif act == 'brand_assign':
            bd = pattern['brand'][0]
            regular_bd = pattern['_regular']['brand'][0]
            status['brand']['in'] = [regular_bd]
            if regular_bd in status['brand']['not']:
                status['brand']['not'].remove(regular_bd)
            msg = random_nlg('brand_assign', {'brand': bd})
        elif act == 'ask_performance':
            msg = perfs.cpu(status['last_products'][0])

    all = search_once(status)
    all.sort(key=lambda p: props.price(p))
    n = len(all)
    v = [all[int(n * status['price_pos'])]]
    status['last_products'] = v
    data = {'error': 0,
            'msg': {
                'products': v,
                'message': msg,
                'status': json.dumps(status, sort_keys=True),
            },
        }
    return json_response(data)

def tips(request):
    data = {'error': 0, 'msg': 'response from backend:tips'}
    return json_response(data)
