#coding=utf8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import scrapy


class SearchSpider(scrapy.Spider):
    name = "search"

    def start_requests(self):
        self.visited_search_list = 0
        self.visited_search_list_max = float('inf')
        self.visited_series = 0
        self.visited_series_max = float('inf')
        urls = [
            'http://detail.zol.com.cn/notebook_index/subcate16_0_list_1_0_99_1_0_1.html',
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.search_list)

    def search_list(self, response):
        for a in response.css('.pro-intro > h3 > a'):
            link = a.css('::attr(href)').extract_first()
            name = a.css('::text').extract_first()
            yield scrapy.Request(response.urljoin(link), callback=self.single_pc)
        next_page = response.css('.pagebar a.next ::attr(href)').extract_first()
        if next_page:
            if self.visited_search_list >= self.visited_search_list_max:
                return
            self.visited_search_list += 1
            yield scrapy.Request(response.urljoin(next_page), callback=self.search_list)

    def single_pc(self, response):
        for a in response.css('.nav li a'):
            title = a.css('::text').extract_first()
            if title is not None:
                if '配置' == title.strip():
                    link = a.css('::attr(href)').extract_first()
                    if link:
                        if self.visited_series >= self.visited_series_max:
                            continue
                        self.visited_series += 1
                        yield scrapy.Request(response.urljoin(link), callback=self.series)

    def series(self, response):
        this_series = response.css('.ptitle ::text').extract_first()
        table = response.css('table#seriesParamTable')
        if len(table) != 1:
            return
        table = table[0]
        all = []
        for i, tr in enumerate(table.css('tr')):
            title = tr.css('th ::text').extract_first()
            if not title:
                continue
            title = title.strip()
            if title == '价格/商家':
                def add_to_dict(key, selector):
                    for idx, v in enumerate(selector):
                        while len(all) <= idx:
                            all.append(dict())
                        all[idx][key] = v.css('::text').extract()
                add_to_dict('price', tr.css('span.price b'))
                add_to_dict('date', tr.css('span.date'))
                add_to_dict('price-status', tr.css('span.price-status'))
                add_to_dict('seller_num', tr.css('p.seller_num a'))
            else:
                for j, td in enumerate(tr.css('td')):
                    while len(all) <= j:
                        all.append(dict())
                    all[j][title] = td.css('::text').extract()
                    if title == '型号':
                        link = td.css('a::attr(href)').extract_first()
                        if link:
                            all[j]['link'] = response.urljoin(link)
                    elif title == '图片':
                        link = td.css('img::attr(src)').extract_first()
                        if link:
                            all[j]['img'] = response.urljoin(link)
        yield {'series': this_series, 'products': all}
