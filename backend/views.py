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

def constraints_in_native(status):
    def native_brand(v):
        v.sort(key=lambda b: (b == 'others', b))
        d = {
            'thinkpad': 'ThinkPad',
            'apple': '苹果',
            'ms': '微软',
            'lenovo': '联想',
            'dell': '戴尔',
            'hasee': '神舟',
            'alien': '外星人',
            'samsung': '三星',
            'hp': '惠普',
            'asus': '华硕',
            'acer': '宏碁',
            }
        return [d[s] for s in v]
    res = []
    if status['brand']['in']:
        res.append('品牌只要{0}'.format('、'.join(native_brand(status['brand']['in']))))
    elif status['brand']['not']:
        res.append('品牌不要{0}'.format('、'.join(native_brand(status['brand']['not']))))
    prop_limits = [
        ('price', '价格{0}{1}元'),
        ('cpu', 'CPU{0}{1}GHz'),
        ('memory', '内存{0}{1}GB'),
        ('disk', '硬盘{0}{1}GB'),
        ('gpu', 'GPU{0} GTX 9{1}0'),
        ('screen', '屏幕{0}{1}寸'),
        ('market_date', '上市时间{0}{1}'),
    ]
    for p in prop_limits:
        rng = status[p[0]]
        if rng[0] is None: continue
        elif rng[0] == 'gt': s0 = '大于'
        elif rng[0] == 'lt': s0 = '小于'
        elif rng[0] == 'gte': s0 = '不小于'
        elif rng[0] == 'lte': s0 = '不大于'
        elif rng[0] == 'eq': s0 = '是'
        else: assert False, rng
        res.append(p[1].format(s0, rng[1]))
    if status['weight'][0] is not None:
        assert status['weight'] == ['lte', 1.5]
        res.append('便携（小于1.5Kg）')
    return '，'.join(res)

def json_response(data):
    return HttpResponse(json.dumps(data), content_type="application/json")

def query(request):
    if request.POST.get('status'):
        status = json.loads(request.POST.get('status'))
    else:
        status = {
                'brand': {'in': None, 'not': []},
                'color': {'in': None, 'not': []},
                'cpu': [None],
                'memory': [None],
                'disk': [None],
                'gpu': [None],
                'screen': [None],
                'weight': [None],
                'battery_life': [None],
                'market_date': [None],
                'price': [None],
                'price_pos': 0.5,
                'config_exist': False,
                }
    def check_between(product, func, rng):
        if type(rng) is not type(dict()) and rng[0] is None:
            return True
        prop = func(product)
        if type(rng) is type(dict()):
            if type(prop) is type(list()):
                for p in prop:
                    if p not in rng['not'] and (rng['in'] is None or p in rng['in']):
                        return True
                return False
            return prop not in rng['not'] and (rng['in'] is None or prop in rng['in'])
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
                if not check_between(p, props.color, status['color']): continue
                if not check_between(p, props.cpu_freq, status['cpu']): continue
                if not check_between(p, props.memory_size, status['memory']): continue
                if not check_between(p, props.disk_size, status['disk']): continue
                if not check_between(p, props.gpu_rank, status['gpu']): continue
                if not check_between(p, props.screen_size, status['screen']): continue
                if not check_between(p, props.weight, status['weight']): continue
                if not check_between(p, props.battery_life, status['battery_life']): continue
                if not check_between(p, props.market_date, status['market_date']): continue
                if not check_between(p, props.price, status['price']): continue
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
            status['config_exist'] = True
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
            status['config_exist'] = True
            regular_bd = pattern['_regular']['brand'][0]
            status['brand']['in'] = [regular_bd]
            if regular_bd in status['brand']['not']:
                status['brand']['not'].remove(regular_bd)
            msg = random_nlg('brand_assign', {'brand': bd})
        # color
        elif act == 'to_ask_color':
            status['config_exist'] = True
            msg = random_nlg('to_ask_color', {})
        elif act == 'color_no':
            cl = pattern['color'][0]
            status['config_exist'] = True
            regular_cl = pattern['_regular']['color'][0]
            if status['color']['in'] is not None and regular_cl in status['color']['in']:
                status['color']['in'].remove(regular_cl)
            if status['color']['in'] is not None and 0 == len(status['color']['in']):
                status['color']['in'] = None
            if regular_cl not in status['color']['not']:
                status['color']['not'].append(regular_cl)
            msg = random_nlg('color_no', {'color': cl})
        elif act == 'color_assign':
            cl = pattern['color'][0]
            status['config_exist'] = True
            regular_cl = pattern['_regular']['color'][0]
            status['color']['in'] = [regular_cl]
            if regular_cl in status['color']['not']:
                status['color']['not'].remove(regular_cl)
            friendly_display(status['color'])
            msg = random_nlg('color_assign', {'color': cl})
        # portable
        elif act == 'portable':
            status['weight'] = ['lte', 1.5]
            status['config_exist'] = True
            if len(search_once(status)) < 1:
                status = old_status
                msg = random_nlg('protable_failed', {})
            else:
                msg = random_nlg('portable', {})
        # long battery life
        elif act == 'long_battery_life':
            status['battery_life'] = ['gte', 5]
            status['config_exist'] = True
            if len(search_once(status)) < 1:
                status = old_status
                msg = random_nlg('long_battery_life_failed', {})
            else:
                msg = random_nlg('long_battery_life', {})
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
        
        if status.get('last_products'):
            # price
            if act == 'price_dec':
                status['price'] = ['lte', props.price(status['last_products'][0]) - 1]
                status['price_pos'] = 0.8
                if len(search_once(status)) < 1:
                    status = old_status
                    msg = random_nlg('price_dec_failed', {})
                else:
                    msg = random_nlg('price_dec', {})
            elif act == 'ask_color':
                msg = random_nlg('ask_color', {'colors': '色、'.join(props.color(status['last_products'][0])) + '色'})
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
                'guarantee': (perfs.guarantee, ),
                'battery': (perfs.battery_life, ),
            }
            if act == 'ask_performance':
                performance = pattern['_regular']['performance'][0]
                perffn = ask_performance[performance][0]
                msg = perffn(status['last_products'][0])

    if status['config_exist'] == False:
        msg = random_nlg('ask_purpose', {})

    all = search_once(status)
    all.sort(key=lambda p: props.price(p))
    n = len(all)
    v = [all[int(n * status['price_pos'])]]
    # friendly_display(v)
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
