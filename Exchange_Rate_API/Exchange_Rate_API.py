import re
import os
import requests
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
from collections import defaultdict
from flask import Flask, jsonify, request, abort
from flask_restful import Api, Resource, reqparse

class Exchange_Rate_API:
    def __init__(self):
        self.get_exchange_rate()

    def get_exchange_rate(self):
        # get data
        self.url = 'https://rate.bot.com.tw/xrt?Lang=zh-TW'
        res = requests.get(self.url)
        soup = BeautifulSoup(res.text, 'html.parser')
        # query date
        self.date = soup.find_all(attrs={'time'})[0].text[0:10]
        # country with chinese
        tmp_country = soup.find_all(attrs={'visible-phone print_hide'})
        # exchange rate
        tmp_exchange_rate = soup.find_all(attrs={"rate-content-cash text-right print_hide"}) 

        self.build_exchange_rate(tmp_exchange_rate, tmp_country)
        self.build_currency(tmp_country)
        self.build_three_month_data()

    def build_exchange_rate(self, tmp_exchange_rate, tmp_country):
        # create exchange rate dictionary
        self.exchange_rate = defaultdict()
        for i, k in zip(np.arange(1, len(tmp_exchange_rate), 2),range(0, len(tmp_country))):
            try:
                self.exchange_rate[re.search('\(.*\)', tmp_country[i].text.strip()).group(0)[1:4]] = float(tmp_exchange_rate[i].text.strip())
            except:
                continue
        self.exchange_rate['TWD'] = 1

    # currency list
    def build_currency(self, tmp_country):
        self.currency = list()
        for i in range(0, len(tmp_country)):
            try:
                self.currency.append(re.search('\(.*\)', tmp_country[i].text.strip()).group(0)[1:4])
            except:
                continue

    # 3 month exchange rate
    def build_three_month_data(self):
        self.three_month = defaultdict(list)
        for i in self.currency:
            res = requests.get(f'https://rate.bot.com.tw/xrt/quote/ltm/{i}')
            soup = BeautifulSoup(res.text,'html.parser')
            tmp = soup.find_all(attrs={'rate-content-cash text-right print_table-cell'})
            for k in np.arange(1, len(tmp), 2):
                self.three_month[i].append(float(tmp[k].text))

# get all rates
class get_all(Resource):
    def get(self):
        return ex.exchange_rate

##############
##   post   ##
##############
class add_currency(Resource):
    def post(self, currency):
        if currency in ex.exchange_rate.keys():
            return f'{currency} is exist'
        else:
            parser = reqparse.RequestParser()
            parser.add_argument('rate', type=int, help='please input rate', required=True)
            arg = parser.parse_args()
            ex.exchange_rate[currency] = arg['rate']
            return ex.exchange_rate[currency]

# get all rates by specific country
class get_all_specific(Resource):
    def get(self, target):
        target_rate = ex.exchange_rate[target]
        other_rate = dict()
        for i in ex.exchange_rate.keys():
            other_rate[i] = round(ex.exchange_rate[i] / target_rate, 2)
        return other_rate

# get the exchange rate: (customer country : travel country)
class get_recommend(Resource):
    def get(self, from_currency, to_currency):
        from_rate = ex.exchange_rate[from_currency]
        to_rate = ex.exchange_rate[to_currency]
        if to_currency == 'TWD':
            target_currency = from_currency
            n, step = 1, 1
        else:
            target_currency = to_currency
            n, step = 5, -1
        rate_scale = np.append(ex.three_month[target_currency].copy(), ex.exchange_rate[target_currency])
        rate_scale = np.unique(rate_scale)
        rate_scale.sort()
        rate_scale = np.where(rate_scale == ex.exchange_rate[target_currency])[0] / len(rate_scale) * 100
        if rate_scale <= 20:
            star = n
        elif rate_scale <= 40:
            star = n + step * 1
        elif rate_scale <= 60:
            star = n + step * 2
        elif rate_scale <= 80:
            star = n + step * 3
        elif rate_scale <= 100:
            star = n + step * 4
        message = {
            'Query Date': ex.date,
            'From': from_currency,
            'To': to_currency,
            'Exchange Rate': f'{str(round(to_rate / from_rate, 2))} {from_currency} exchange 1 {to_currency}',
            'Recommended Level': star
        }
        return message

if __name__ == "__main__":
    ex = Exchange_Rate_API()
    
    app = Flask(__name__)
    api = Api(app)

    parser = reqparse.RequestParser()
    parser.add_argument('rate', type=int, help='wrong rate')

    api.add_resource(get_all, '/exchange_rate/')
    api.add_resource(get_all_specific, '/exchange_rate/<string:target>')
    api.add_resource(get_recommend, '/exchange_rate/<string:from_currency>/<string:to_currency>')
    api.add_resource(add_currency, '/exchange_rate/add_currency/<string:currency>')

    app.run(host='0.0.0.0', port=8889, debug=True)