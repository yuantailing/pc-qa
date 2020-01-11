#coding=utf8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import json
import csv, codecs, cStringIO

class UnicodeWriter:
    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        # Redirect output to a queue
        self.queue = cStringIO.StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, row):
        self.writer.writerow([s.encode("utf-8") if s is not None else s for s in row])
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data) if data is not None else data
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)

def run(input_filename, output_filename):
    with open(input_filename) as f:
        data = json.load(f)
    known_attr = ['型号', 'price', 'date', 'price-status', 'seller_num'] + \
        ['上市时间', '产品类型', '产品定位', '超极本特性', '操作系统'] + \
        ['CPU系列', 'CPU型号', 'CPU主频', '最高睿频', '核心/线程数', '三级缓存', '核心架构', '制程工艺', '功耗'] + \
        ['内存容量', '内存类型', '硬盘容量', '硬盘描述', '光驱类型'] + \
        ['触控屏', '屏幕尺寸', '显示比例', '屏幕分辨率', '屏幕技术'] + \
        ['显卡类型', '显卡芯片', '显存容量', '显存类型', '显存位宽'] + \
        ['摄像头', '音频系统', '扬声器', '麦克风'] + \
        ['无线网卡', '蓝牙'] + \
        ['数据接口', '音频接口', '其它接口', '读卡器'] + \
        ['指取设备', '键盘描述', '指纹识别'] + \
        ['电池类型', '续航时间', '电源适配器'] + \
        ['笔记本重量', '长度', '宽度', '厚度', '外壳材质', '外壳描述'] + \
        ['安全性能', '附带软件', '其它特点'] + \
        ['保修政策', '质保时间', '质保备注', '客服电话', '电话备注']
    with open(output_filename, 'wb') as csvfile:
        csvfile.write(b'\xef\xbb\xbf')
        spamwriter = UnicodeWriter(csvfile, dialect=csv.excel, quoting=csv.QUOTE_MINIMAL)
        spamwriter.writerow(['series'] + known_attr)
        for a in data:
            series = a['series'].strip()
            assert(series[-2:] == '配置')
            series = series[:-2]
            for p in a['products']:
                attrs = map(lambda k: '\n'.join(p[k]) if k in p else None, known_attr)
                spamwriter.writerow([series] + attrs)

if __name__ == '__main__':
    run('search.json', 'search.csv')
