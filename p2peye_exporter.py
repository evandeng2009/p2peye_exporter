#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import requests
from lxml import html
from flask import Flask, Response

from prometheus_client import Info, Gauge, generate_latest
from prometheus_client.core import CollectorRegistry


# Basic info
github_repo = 'https://github.com/evandeng2009/p2peye_exporter'
update_date = '2019-01-28'

# Set constant
VERIFICATION_FAILED = '<html>fakehtml</html>'
DEFAULT_PROPERTY = ['无']

# Set Flask app
app = Flask(__name__)


# Get app port
def get_port():
    if 'p2peye_port' in os.environ.keys():
        app_port = os.environ.get('p2peye_exporter_port')
    else:
        app_port = 8087
    return app_port


# Get date or time string
def get_datetime(t):
    if t == 'date':
        # 20190201
        return time.strftime('%Y%m%d', time.localtime(time.time()))
    elif t == 'time':
        # 2019-02-01 19:16:50
        return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))


# Log
def logger(level, msg):
    print('[' + get_datetime('time') + ']' + '[' + level.upper() + ']', msg)


# Sign in
def sign_in():
    # Guest will have p2peye tickets which actually not suitable for signed in users who have already invested before
    # Besides those tickets are not all available for even a newly registered user
    # So firstly sign in and then scrape those rebates
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-CN,en-US;q=0.7,en;q=0.3',
        'Connection': 'keep-alive',
        'Content-Length': '82',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'DNT': '1',
        'Host': 'www.p2peye.com',
        'Referer': 'https://licai.p2peye.com/rebate/?order=1&status=1&type=1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:64.0) Gecko/20100101 Firefox/64.0',
        'X-Requested-With': 'XMLHttpRequest'
    }
    signin_url = 'https://www.p2peye.com/member.php?mod=login_ty&action=login_ty_ajax&loginsubmit=yes'
    global user_name
    global user_password
    user_name = 'p2peye_user_name'
    user_password = 'p2peye_user_password_in_browser_request'
    signin_data = {
        "ymz": "1",
        "username": user_name,  # User name or cell phone number in request form
        "password": user_password,  # Password in request form
        "showpassword": ""
    }
    global s
    s = requests.Session()
    r = s.post(signin_url, data=signin_data, headers=headers, timeout=10, allow_redirects=True)


# Send http GET request and return XML
def send_request(url):
    global s
    try:
        response = s.get(url, timeout=5, allow_redirects=False)
        if response.status_code == 302:
            return VERIFICATION_FAILED
        return response.text
    except Exception as e:
        logger('error', e)
        return VERIFICATION_FAILED


# xPath via eTree to get specified content value
def etree_value(obj, url, xpath_list, t='xml'):
    # Support both XML and eTree
    if t == 'xml':
        etree = html.etree.HTML(obj)
    elif t == 'etree':
        etree = obj
    xpath_length = len(xpath_list)
    i = 0
    for x in xpath_list:
        result = etree.xpath(x)
        if len(result) != 0:
            # Return an array, coz of returned value may be also an etree
            return result
        else:
            # The last xpath then no match found
            if i == xpath_length - 1:
                if xpath_list == ['/html/body/div[6]/div[1]/div/div[3]/a/text()']:
                    pass
                else:
                    logger('warn', 'no value got for xpath ' + x + ' from ' + url + ', maybe html structure changed')
                return DEFAULT_PROPERTY
        i += 1


# Get vendors
def get_vendors(for_beginner):
    # First or second investment
    if for_beginner == 'yes':
        url = 'https://licai.p2peye.com/rebate/?order=1&type=1&status=1'
    else:
        url = 'https://licai.p2peye.com/rebate/?order=1&type=2&status=1'
    vendor_lis_xpath1 = '/html/body/div[6]/div[3]/div[2]/ul/li'
    vendor_lis_xpath2 = '/html/body/div[6]/div[2]/div[2]/ul/li'
    vendor_href_xpath = 'div[4]/a/@href'
    vendors_urls = []
    # Get XML
    response_xml = send_request(url)
    if not response_xml:
        return vendors_urls
    vendors_etree = html.etree.HTML(send_request(url))
    vendors_lis = vendors_etree.xpath(vendor_lis_xpath1)
    if len(vendors_lis) == 0:
        vendors_lis = vendors_etree.xpath(vendor_lis_xpath2)
    for vendor_li in vendors_lis:
        vendor_href = vendor_li.xpath(vendor_href_xpath)
        if len(vendor_href) != 0:
            # https://licai.p2peye.com/rebate/4318-2-1.html
            vendors_urls.append('https://licai.p2peye.com' + vendor_href[0])
    if len(vendors_urls) == 0:
        logger('warn', 'no vendor found, maybe html structure changed')
    return vendors_urls  # It's an array


@app.route('/')
def redirect():
    return '<a href=metrics>Metrics</a>'


# Define and set metrics value
@app.route('/metrics')
def prom_exporter():
    # Sign in first
    sign_in()
    vendor_xpath = ['/html/body/div[7]/div[1]/div/div[1]/div/div[2]/div[1]/div/a/text()',
                    '/html/body/div[6]/div[1]/div/div[1]/div/div[2]/div[1]/div/a/text()']
    location_xpath = ['/html/body/div[7]/div[1]/div/div[1]/div/div[2]/ul/li[3]/text()',
                      '/html/body/div[6]/div[1]/div/div[1]/div/div[2]/ul/li[3]/text()']
    online_date_xpath = ['/html/body/div[7]/div[1]/div/div[1]/div/div[2]/ul/li[2]/text()',
                         '/html/body/div[6]/div[1]/div/div[1]/div/div[2]/ul/li[2]/text()']
    registered_capital_xpath = ['/html/body/div[7]/div[1]/div/div[1]/div/div[2]/ul/li[1]/span[2]/text()',
                                '/html/body/div[6]/div[1]/div/div[1]/div/div[2]/ul/li[1]/span[2]/text()']
    vendor_href_xpath = ['/html/body/div[7]/div[1]/div/div[1]/div/div[1]/div[1]/a/@href',
                         '/html/body/div[6]/div[1]/div/div[1]/div/div[1]/div[1]/a/@href']

    durations_divs_xpath1 = '/html/body/div[7]/div[1]/div/div[3]/div'  # Begin with [2]
    durations_divs_xpath2 = '/html/body/div[6]/div[1]/div/div[3]/div'  # Begin with [2]
    durations_divs_xpath3 = '/html/body/div[6]/div[1]/div/div[4]/div'  # Begin with [2], for 2nd investment in 1st one
    duration_h_xpath = ['div/h4/text()']
    global beginner_p_xpath
    beginner_p_xpath = 'div/p'
    solutions_lis_xpath = 'ul/li'

    solution_name_div_xpath = ['div[1]/div/text()']
    solution_min_amount_span_xpath = ['div[2]/div[1]/div[1]/span[1]/text()']
    solution_all_roi_span_xpath = ['div[2]/div[2]/div[1]/span[1]/text()']
    solution_all_roi_rate_span_xpath = ['div[2]/div[3]/div[1]/span/text()']
    solution_p2peye_return_span_xpath = ['div[2]/div[4]/div[1]/span[1]/text()',
                                         'div[2]/div[3]/div[1]/span[1]/text()']
    # Create a metric registry
    registry = CollectorRegistry()
    # Define metrics
    i = Info('build', '', registry=registry)
    i.info({'version': update_date, 'github': github_repo})
    g_p2peye_rebate = Gauge('p2peye_rebate', 'P2peye rebates',
                            ['user', 'vendor', 'location', 'online_date', 'registered_capital', 'url', 'comment_url',
                             'duration', 'beginner_flag', 'solution', 'min_amount', 'all_roi', 'all_roi_rate',
                             'p2peye_return', 'return_per_day'], registry=registry)

    # Separately get rebates for beginners and not
    def scrape_rebates(urls, for_beginner):
        # Get metric properties
        for vendor_url in urls:
            # Get XML
            response_xml = send_request(vendor_url)
            if not response_xml:
                continue
            # Assign basic properties of vendor
            property_user = user_name
            property_vendor = etree_value(response_xml, vendor_url, vendor_xpath)[0]
            property_location = etree_value(response_xml, vendor_url, location_xpath)[1].split('\n')[0]
            property_online_date = etree_value(response_xml, vendor_url, online_date_xpath)[1].split('\n')[0]
            property_registered_capital = etree_value(response_xml, vendor_url, registered_capital_xpath)[0]
            if property_registered_capital != DEFAULT_PROPERTY[0]:
                property_registered_capital = str(round(float(property_registered_capital) * 10000))  # 10000 as unit
            property_url = vendor_url
            property_comment_url = 'https:' + etree_value(response_xml, vendor_url, vendor_href_xpath)[0] + '/comment/'
            # Assign detailed properties of specific rebate
            durations_etree = html.etree.HTML(response_xml)  # durations_solutions
            if for_beginner == 'yes' and etree_value(
                    response_xml, vendor_url, ['/html/body/div[6]/div[1]/div/div[3]/a/text()'])[0].find('多次') != -1:
                    durations_divs = durations_etree.xpath(durations_divs_xpath3)
            else:
                durations_divs = durations_etree.xpath(durations_divs_xpath1)
                if len(durations_divs) == 0:
                    durations_divs = durations_etree.xpath(durations_divs_xpath2)
            for i in range(1, len(durations_divs)):  # Begin with [1]
                property_duration = etree_value(durations_divs[i], vendor_url, duration_h_xpath, 'etree')[0]
                if for_beginner == 'yes':
                    property_beginner_flag = '是'
                elif for_beginner == 'no':
                    property_beginner_flag = '否'
                solutions_lis = durations_divs[i].xpath(solutions_lis_xpath)
                # Get properties of a specific solution
                for solution_li in solutions_lis:
                    property_solution_name = etree_value(solution_li, vendor_url, solution_name_div_xpath, 'etree')[0]
                    property_min_amount = etree_value(solution_li, vendor_url, solution_min_amount_span_xpath, 'etree')[0]
                    property_all_roi = etree_value(solution_li, vendor_url, solution_all_roi_span_xpath, 'etree')[0]
                    property_all_roi_rate = str(
                        etree_value(solution_li, vendor_url, solution_all_roi_rate_span_xpath, 'etree')[0]) + '%'
                    property_p2peye_return = etree_value(solution_li, vendor_url, solution_p2peye_return_span_xpath, 'etree')[0]
                    # Get metrics values
                    # Assign metrics values
                    # Compute return_per_day
                    if property_all_roi != DEFAULT_PROPERTY[0] and property_min_amount != DEFAULT_PROPERTY[0] \
                            and property_duration != DEFAULT_PROPERTY[0]:
                        property_10k = float(property_min_amount) / 10000
                        property_day = property_duration.replace('个', '').replace('及以上', '')
                        if property_day.find('天') != -1:
                            property_day = int(property_day.replace('天', ''))
                        elif property_day.find('月') != -1:
                            property_day = int(property_day.replace('月', '')) * 30
                        elif property_day.find('年') != -1:
                            property_day = int(property_day.replace('年', '')) * 365
                        # Return per day per 10k
                        property_return_per_day = str(round(float(property_all_roi) / property_day / property_10k, 2))
                    else:
                        property_return_per_day = DEFAULT_PROPERTY[0]
                    g_p2peye_rebate.labels(
                        user=property_user, vendor=property_vendor, location=property_location, online_date=property_online_date,
                        registered_capital=property_registered_capital, url=property_url, comment_url=property_comment_url,
                        duration=property_duration, beginner_flag=property_beginner_flag, solution=property_solution_name,
                        min_amount=property_min_amount, all_roi=property_all_roi, all_roi_rate=property_all_roi_rate,
                        p2peye_return=property_p2peye_return, return_per_day=property_return_per_day).set(1)
    scrape_rebates(get_vendors(for_beginner='yes'), for_beginner='yes')
    scrape_rebates(get_vendors(for_beginner='no'), for_beginner='no')
    # Respond with metrics
    return Response(generate_latest(registry), mimetype="text/plain")


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=get_port())
