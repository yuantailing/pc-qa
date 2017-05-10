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
                'brand': {'in': None, 'not': []},
                'cpu': [None],
                'memory': [None],
                'disk': [None],
                'gpu': [None],
                'screen': [None],
                'weight': [None],
                'market_date': [None],
                'price': [None],
                'seller': [None],
                'price_pos': 0.5,
                'config_exist': False,
                }
    def check_between(product, func, rng):
        if type(rng) is not type(dict()) and rng[0] is None:
            return True
        prop = func(product)
        if type(rng) is type(dict()): return prop not in rng['not'] and (rng['in'] is None or prop in rng['in'])
        if rng[0] == 'gt': return prop is not None and prop > rng[1]
        if rng[0] == 'lt': return prop is not None and prop < rng[1]
        if rng[0] == 'gte': return prop is not None and prop >= rng[1]
        if rng[0] == 'lte': return prop is not None and prop <= rng[1]
        if rng[0] == 'eq': return prop is not None and prop == rng[1]
        raise ValueError(rng)
    def search_once(status):
        all = []
        for s in series:
            for p in s['products']:
                if props.is_ill(p): continue
                if not check_between(p, props.brand, status['brand']): continue
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
        # brand
        if act == 'brand_no':
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
        # portable
        elif act == 'portable':
            status['weight'] = ['lte', 1.5]
            status['config_exist'] = True
            if len(search_once(status)) < 1:
                status = old_status
                msg = random_nlg('protable_failed', {})
            else:
                msg = random_nlg('portable', {})
        # application
        elif act == 'low_demand':
            status['price_pos'] = 0.25
            status['config_exist'] = True
            msg = random_nlg('demand_level', {'level': '入门'})
        elif act == 'medium_demand':
            status['price_pos'] = 0.5
            status['config_exist'] = True
            msg = random_nlg('demand_level', {'level': '大众'})
        elif act == 'high_demand':
            status['price_pos'] = 0.75
            status['config_exist'] = True
            msg = random_nlg('demand_level', {'level': '高端'})
        # price
        elif act == 'price_dec':
            status['price'] = ['lte', props.price(status['last_products'][0]) - 1]
            status['price_pos'] = 0.8
            if len(search_once(status)) < 1:
                status = old_status
                msg = random_nlg('price_dec_failed', {})
            else:
                msg = random_nlg('price_dec', {})
        elif act == 'ask_guarantee':
            if status['last_products']:
                msg = random_nlg('guarantee', {'text': props.guarantee(status['last_products'][0])})
        # without config
        elif act =='recommend_without_config':
            msg = random_nlg('ask_purpose', {})

        constraints_adjust_settings = {
            # NLU里的关键词:  (status里的键  props里的函数  (inc成功NLG参数  失败NLG参数), (dec成功NLG参数  失败NLG参数))
            'cpu': ('cpu', props.cpu_freq, ('cpu更好', ), ('cpu稍弱', )),
            'memory': ('memory', props.memory_size, ('内存更大', ), ('内存稍小', )),
            'disk': ('disk', props.disk_size, ('硬盘更大', ), ('硬盘更小', )),
            'gpu': ('gpu', props.gpu_rank, ('gpu更好', ), ('gpu稍弱', )),
            'screen': ('screen', props.screen_size, ('屏幕更大', ), ('屏幕更小', )),
        }
        if act in ('property_inc', 'property_dec'):
            property = pattern['_regular']['property'][0]
            statuskey, propfn, incnlgparam, decnlgparam = constraints_adjust_settings[property]
            if act.endswith('inc'):
                direction, pricepos, nlgparam = 'gt', 0.2, incnlgparam
            else:
                direction, pricepos, nlgparam = 'lt', 0.8, decnlgparam
            if status['last_products']:
                status[statuskey] = [direction, propfn(status['last_products'][0])]
                status['price_pos'] = pricepos
                status['config_exist'] = True
                if len(search_once(status)) < 1:
                    status = old_status
                    msg = random_nlg('config_change_failed', {'item_change': nlgparam[1] if len(nlgparam) > 1 else nlgparam[0]})
                else:
                    msg = random_nlg('config_change', {'item_change': nlgparam[0]})

        ask_performance = {
            'cpu': (perfs.cpu, ),
            'gpu': (perfs.gpu, ),
        }
        if act == 'ask_performance':
            performance = pattern['_regular']['performance'][0]
            perffn = ask_performance[performance][0]
            if status['last_products']:
                msg = perffn(status['last_products'][0])

    if status['config_exist'] == False:
        msg = random_nlg('ask_purpose', {})

    all = search_once(status)
    all.sort(key=lambda p: props.price(p))
    n = len(all)
    v = [all[int(n * status['price_pos'])]]
    friendly_display(v)
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
