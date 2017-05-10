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
