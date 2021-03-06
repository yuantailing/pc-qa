#coding=utf8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import json
import re
from functools import reduce


strict_policy = True

def friendly_display(obj):
    print(json.dumps(obj, ensure_ascii=False, indent=None, sort_keys=True))

def is_ill(product):
    if price(product) is None: return True
    if 'CPU型号' not in product or len(product['CPU型号']) == 0: return True
    if 'CPU主频' not in product or len(product['CPU主频']) == 0: return True
    if '内存容量' not in product or len(product['内存容量']) == 0: return True
    if '硬盘容量' not in product or len(product['硬盘容量']) == 0: return True
    if '显卡芯片' not in product or len(product['显卡芯片']) == 0: return True
    if '显存容量' not in product or len(product['显存容量']) == 0: return True
    if '笔记本重量' not in product or len(product['笔记本重量']) == 0: return True
    if '上市时间' not in product or len(product['上市时间']) == 0: return True
    if '外壳描述' not in product or len(product['外壳描述']) == 0: return True
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
    if s.startswith('锡恩帝'): return 'others'
    if strict_policy: raise ValueError(s)
    return 'others'

def cpu_freq(product): # GHz
    s = product['CPU主频'][0]
    if re.match('^(\d(?:\.\d+)?)GHz$', s): return float(re.match('(\d(?:\.\d+)?)GHz', s).group(1))
    if re.match('^(\d+)MHz$', s): return int(re.match('(\d+)MHz', s).group(1)) * 0.001
    if strict_policy: raise ValueError(s)
    return 0

def memory_size(product): # GB
    s = product['内存容量'][0]
    if re.match('^(\d+)GB', s): return int(re.match('(\d+)GB', s).group(1))
    if re.match('^512MB', s): return 0.5
    if strict_policy: raise ValueError(s)
    return 0

def disk_size(product): # GB
    s = product['硬盘容量'][0]
    if re.match('^(\d+(?:\.\d+)?)(?:TB|TGB)$', s): return int(float(re.match('^(\d+(?:\.\d+)?)(?:TB|TGB)$', s).group(1)) * 1000)
    if re.match('^(\d+)GB(?: SSD固态硬盘)?$', s): return int(re.match('^(\d+)GB(?: SSD固态硬盘)?$', s).group(1))
    if re.match('^(?:2×)?(\d+)GB\+(\d+(?:\.\d+)?)TB', s): return int(float(re.match('^(?:2×)?(\d+)GB\+(\d+(?:\.\d+)?)TB', s).group(2)) * 1000)
    if re.match('^2×(\d+)GB$', s): return int(re.match('^2×(\d+)GB$', s).group(1)) * 2
    if re.match('^2×(\d+)TB$', s): return int(re.match('^2×(\d+)TB$', s).group(1)) * 1000 * 2
    if re.match('^(\d+)GB\+(\d+)GB', s): return max(int(re.match('^(\d+)GB\+(\d+)GB', s).group(1)), int(re.match('^(\d+)GB\+(\d+)GB', s).group(2)))
    if re.match('^(\d+)TB\+(\d+)TB', s): return max(int(re.match('^(\d+)TB\+(\d+)TB', s).group(1)), int(re.match('^(\d+)TB\+(\d+)TB', s).group(2))) * 1000
    if re.match('^(\d+)TB\+(\d+)GB', s): return int(re.match('^(\d+)TB\+(\d+)GB', s).group(1)) * 1000
    if re.match('^(\d+(?:\.\d+)?)$', s): return int(float(re.match('^(\d+(?:\.\d+)?)$', s).group(1)))
    if strict_policy: raise ValueError(s)
    return 0

def gpu_rank(product):
    s = product['显卡芯片'][0]
    if re.search('(?:GTX|Geforce|GeForce|GT) (\d+)', s): return int(re.search('(?:GTX|Geforce|GeForce|GT) (\d+)', s).group(1)[-2])
    s = product['显存容量'][0]
    if re.search('(?:\d+)M', s): return 0
    if s in ('共享内存容量', '共享系统内存', '共享系统内存容量', '动态共享内存'): return 0
    if re.match('^(\d)GB$', s): return {1:2, 2:4, 4:6, 8:8}[int(re.match('^(\d)GB$', s).group(1))]
    if strict_policy: raise ValueError(s)
    return 0

def screen_size(product):
    s = product['屏幕尺寸'][0]
    if re.match('^(\d+(?:\.\d)?)英寸$', s): return float(re.match('^(\d+(?:\.\d)?)英寸$', s).group(1))
    if strict_policy: raise ValueError(s)
    return 0

def weight(product): # Kg
    s = product['笔记本重量'][0]
    if re.match('^(\d+(?:\.\d+)?)Kg$', s): return float(re.match('^(\d+(?:\.\d+)?)Kg$', s).group(1))
    if re.match('^(\d+)g$', s): return float(re.match('^(\d+)g$', s).group(1)) * 0.001
    if strict_policy: raise ValueError(s)
    return 0

def market_date(product): # YYYYMM
    s = product['上市时间'][0]
    if re.match('^(\d{4})年(\d{1,2})(?:月)?$', s): return int(re.match('^(\d{4})年(\d{1,2})(?:月)?$', s).group(1)) * 100 + int(re.match('^(\d{4})年(\d{1,2})(?:月)?$', s).group(2))
    if re.match('^(\d{4})(?:年)?$', s): return int(re.match('^(\d{4})(?:年)?$', s).group(1)) * 100
    if strict_policy: raise ValueError(s)
    return 0

def price(product):
    s = product['price'][0]
    if re.match('^\d+$', s):
        return int(s)
    elif re.match('^(\d+(?:\.\d+)?)万$', s):
        return int(float(re.match('^(\d+(?:\.\d+)?)万$', s).group(1)) * 10000)
    else:
        return None

def seller_num(product):
    s = product['seller_num'][0]
    if re.match('^(\d+)商家在售$', s): return int(re.match('^(\d+)商家在售$', s).group(1))
    return None

_matched_colors = [('^(?:白|珍珠白|象牙白)', '白'), ('^(?:黑|深黑|矿物黑|超炫黑)', '黑'), ('^(?:银|皓月银|魔幻银)', '银'), ('^(?:金|香槟金)', '金'), ('^(?:灰|深灰|深空灰)', '灰'),
    ('^红', '红'), ('绿', '绿'), ('黄|古铜', '黄'), ('蓝', '蓝'), ('橙', '橙'), ('粉', '粉'), ('紫', '紫'), ('棕', '棕'),
    ('红', '红'), ('银', '银'), ('灰', '灰'), ('白', '白'), ('黑|拥有“龙”|魔兽世界定制|顶盖材料:镁|NBA.*(?:球星|球队|特色)', '黑'), ('金', '金'), ('彩', '彩')]
_matched_colors = [(re.compile(t[0]), t[1]) for t in _matched_colors]
def color(product):
    s = product['外壳描述'][0].split('/')
    s = [c.split('，') for c in s]
    s = reduce(lambda a, b: a + b, s)
    res = []
    for t in s:
        for c in _matched_colors:
            if c[0].search(t):
                res.append(c[1])
                break
    if strict_policy: assert res
    return res

def battery_life(product):
    s = product['续航时间'][0]
    if re.match('^(?:\>)?(\d+(?:\.\d+)?)小时', s): return float(re.match('^(?:\>)?(\d+(?:\.\d+)?)小时', s).group(1))
    if re.match('^(\d+(?:\.\d+)?)-(\d+(?:\.\d+)?)小时', s): return float(re.match('^(\d+(?:\.\d+)?)-(\d+(?:\.\d+)?)小时', s).group(1))
    return None
