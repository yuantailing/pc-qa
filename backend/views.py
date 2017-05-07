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

def is_ill(product):
    if price(product) is None: return True
    if 'CPU型号' not in product or len(product['CPU型号']) == 0: return True
    if 'CPU主频' not in product or len(product['CPU主频']) == 0: return True
    if '内存容量' not in product or len(product['内存容量']) == 0: return True
    if '硬盘容量' not in product or len(product['硬盘容量']) == 0: return True
    if '显卡芯片' not in product or len(product['显卡芯片']) == 0: return True
    if '显存容量' not in product or len(product['显存容量']) == 0: return True
    return False

def brand(product):
    s = product['型号'][0].strip()
    if s.lower().find('thinkpad') != -1: return 'thinkpad'
    if s.startswith('苹果'): return 'apple'
    if s.startswith('微软'): return 'ms'
    if s.startswith('联想'): return 'lenovo'
    if s.startswith('戴尔'): return 'dell'
    if s.startswith('神舟'): return 'hasee'
    if s.startswith('Alienware'): return 'alien'
    if s.startswith('三星'): return 'samsung'
    if s.startswith('惠普'): return 'hp'
    if s.startswith('华硕'): return 'asus'
    if s.startswith('Acer'): return 'acer'
    if s.startswith('小米'): return 'others'
    if s.startswith('msi微星'): return 'others'
    if s.startswith('华为'): return 'others'
    if s.startswith('MECHREVO'): return 'others'
    if s.startswith('炫龙'): return 'others'
    if s.startswith('雷神'): return 'others'
    if s.startswith('酷比'): return 'others'
    if s.startswith('LG'): return 'others'
    if s.startswith('昂达'): return 'others'
    if s.startswith('机械师'): return 'others'
    if s.startswith('Terrans'): return 'others'
    if s.startswith('东芝'): return 'others'
    if s.startswith('Daoker'): return 'others'
    if s.startswith('Razer'): return 'others'
    if s.startswith('富士通'): return 'others'
    if s.startswith('技嘉'): return 'others'
    if s.startswith('HIPAA'): return 'others'
    if s.startswith('索尼'): return 'others'
    raise ValueError(s)

def cpu_freq(product): # GHz
    s = product['CPU主频'][0]
    if re.match('^(\d(?:\.\d+)?)GHz$', s): return float(re.match('(\d(?:\.\d+)?)GHz', s).group(1))
    if re.match('^(\d+)MHz$', s): return int(re.match('(\d+)MHz', s).group(1)) * 0.001
    raise ValueError(s)

def memory_size(product): # GB
    s = product['内存容量'][0]
    if re.match('^(\d+)GB', s): return int(re.match('(\d+)GB', s).group(1))
    if re.match('^512MB', s): return 0.5
    raise ValueError(s)

def disk_size(product): # GB
    s = product['硬盘容量'][0]
    if re.match('^(\d+(?:\.\d+)?)(?:TB|TGB)$', s): return int(float(re.match('^(\d+(?:\.\d+)?)(?:TB|TGB)$', s).group(1)) * 1000)
    if re.match('^(\d+)GB$', s): return int(re.match('^(\d+)GB$', s).group(1))
    if re.match('^(?:2×)?(\d+)GB\+(\d+(?:\.\d+)?)TB$', s): return int(float(re.match('^(?:2×)?(\d+)GB\+(\d+(?:\.\d+)?)TB$', s).group(2)) * 1000)
    if re.match('^2×(\d+)TB$', s): return int(re.match('^2×(\d+)TB$', s).group(1)) * 2
    if re.match('^(\d+)GB\+(\d+)GB$', s): return max(int(re.match('^(\d+)GB\+(\d+)GB$', s).group(1)), int(re.match('^(\d+)GB\+(\d+)GB$', s).group(2)))
    if re.match('^(\d+)TB\+(\d+)TB$', s): return max(int(re.match('^(\d+)TB\+(\d+)TB$', s).group(1)), int(re.match('^(\d+)TB\+(\d+)TB$', s).group(2))) * 1000
    if re.match('^(\d+)TB\+(\d+)GB$', s): return int(re.match('^(\d+)TB\+(\d+)GB$', s).group(1)) * 1000
    raise ValueError(s)

def gpu_rank(product):
    s = product['显卡芯片'][0]
    if re.search('(?:GTX|Geforce|GeForce|GT) (\d+)', s): return int(re.search('(?:GTX|Geforce|GeForce|GT) (\d+)', s).group(1)[1])
    s = product['显存容量'][0]
    if re.search('(?:\d+)M', s): return 0
    if s in ('共享内存容量', '共享系统内存', '共享系统内存容量', '动态共享内存'): return 0
    if re.match('^(\d)GB$', s): return {1:2, 2:4, 4:6, 8:8}[int(re.match('^(\d)GB$', s).group(1))]
    raise ValueError(s)

def price(product):
    s = product['price'][0]
    if re.match('^\d+$', s):
        return int(s)
    elif re.match('^(\d+(?:\.\d+)?)万$', s):
        return int(float(re.match('^(\d+(?:\.\d+)?)万$', s).group(1)) * 10000)
    else:
        return None

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
                'price': {'gte': None, 'lte': 7000},
                'price_pos': 0.5,
                }
    def check_between(prop, stat):
        if stat['gte'] is not None and (prop is None or prop < stat['gte']): return False
        if stat['lte'] is not None and (prop is None or prop > stat['lte']): return False
        return True
    def search_once(status):
        all = []
        for s in series:
            for p in s['products']:
                if is_ill(p): continue
                if status['brand']['in'] is not None and brand(p) not in status['brand']['in']: continue
                if brand(p) in status['brand']['not']: continue
                if not check_between(cpu_freq(p), status['cpu']): continue
                if not check_between(memory_size(p), status['memory']): continue
                if not check_between(disk_size(p), status['disk']): continue
                if not check_between(gpu_rank(p), status['gpu']): continue
                if not check_between(price(p), status['price']): continue
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
            if 0 == len(search_once(status)):
                status = old_status
                msg = random_nlg('price_dec_failed', {})
            else:
                msg = random_nlg('price_dec', {})
        elif act == 'brand_no':
            bd = pattern['brand']
            regular_bd = pattern['_regular']['brand'][0]
            if regular_bd not in status['brand']['not']:
                status['brand']['not'].append(regular_bd)
            msg = random_nlg('brand_no', {'brand': bd})

    all = search_once(status)
    all.sort(key=lambda p: price(p))
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
