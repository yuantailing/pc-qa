#coding=utf8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import localqa
import os
import random
from . import props

api = localqa.api.Api(os.path.join(os.path.dirname(__file__), 'config'))

def random_nlg(act_type, kw):
    all = api.nlg(act_type, kw)['msg']
    assert(0 < len(all))
    return random.sample(all, 1)[0]['output']

def cpu(product):
    return random_nlg('perf_cpu_medium', {'name': product['CPU型号'][0], 'freq': product['CPU主频'][0]})

def gpu(product):
    return random_nlg('perf_gpu_medium', {'name': product['显卡芯片'][0], 'freq': product['显存容量'][0]})

def guarantee(product):
    msg = ''
    if not product['质保时间']:
        msg = '没有质保相关信息'
    else:
        msg = product['质保时间'][0]
        if product['质保备注']:
            msg += '：' + product['质保备注'][0]
    return random_nlg('guarantee', {'text': msg})

def battery_life(product):
    return random_nlg('battery_life', {'text': product['续航时间'][0]})
