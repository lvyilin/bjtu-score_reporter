# -*- coding: utf-8 -*-
import urllib.request
import urllib.error
import urllib.parse
import bs4
import http.cookiejar
import gzip
import re
import getpass
import os
import webbrowser

print(r"""
------------------------------------
|  A elegant way to get exam score |
|                                  |
|   Dependency: beautiful soup     |
------------------------------------
""")
USERNAME = input("Please input your bjtu MIS username:")
PASSWORD = getpass.getpass("Please input password (your password will be hidden): ")
CMS_URL = 'https://mis.bjtu.edu.cn/cms/'
HOME_URL = 'https://mis.bjtu.edu.cn/home/'
LOGIN_URL = 'https://mis.bjtu.edu.cn/auth/login/'
TEMP_URL = 'https://mis.bjtu.edu.cn/module/module/311/'
RES_URL = 'https://dean.bjtu.edu.cn/score/scores/stu/view/'

print('Please waiting...')

class Link(object):

    def __init__(self, url, refer_link=None, post_data=None):
        self.url = url
        self.refer_link = refer_link
        self.header = self._build_header(refer_link)
        self.hadaccessed = False
        self.page_content = None
        self.post_data = post_data

    def _build_header(self, refer_url=None):
        headers = {
            'User-Agent': r'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:51.0) Gecko/20100101 Firefox/51.0',
            'Connection': 'keep-alive',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'Upgrade-Insecure-Requests': '1'
        }
        if refer_url:
            headers['Referer'] = refer_url
        return headers

    def print_link(self):
        print('URL: %s' % self.url)

    def access(self):
        headers = self.header
        request = urllib.request.Request(self.url, self.post_data, self.header)
        response = opener.open(request)
        self.hadaccessed = True
        self.response = response
        return self

    def ungzip(self):
        if self.hadaccessed:
            result_b = gzip.decompress(self.response.read())
            self.page_content = str(result_b, 'utf-8')
        return self.page_content


def grade_point(grade):
    level = ('A', 'A-', 'B+', 'B', 'B-', 'C+',
             'C', 'C-', 'D+', 'D', 'F+', 'F')
    point = (range(90, 101), range(85, 90), range(81, 85), range(78, 81), range(75, 78), range(
        72, 75), range(68, 72), range(65, 68), range(63, 65), range(60, 63), range(40, 60), range(0, 40))
    gp = (4.0, 3.7, 3.3, 3.0, 2.7, 2.3, 2.0, 1.7, 1.3, 1.0, 0, 0)
    if grade in level:
        for i in range(0, 12):
            if grade == level[i]:
                return gp[i]
        return 0
    elif grade.isdigit():
        grade = int(grade)
        for i in range(0, 12):
            if grade in point[i]:
                return gp[i]
        return 0
    else:
        return 0

#-----------------------------
#
# begin fetch exam score page
#
#-----------------------------

# cookie perpare
cookie_filename = 'cookies.txt'
cookie = http.cookiejar.MozillaCookieJar(cookie_filename)
handler = urllib.request.HTTPCookieProcessor(cookie)
opener = urllib.request.build_opener(handler)
# -----------
Link(CMS_URL).access()

# prepare login data
for item in cookie:
    if item.name == 'csrftoken':
        CSRFTOKEN = item.value
post_form = {'loginname': USERNAME, 'password': PASSWORD,
             'csrfmiddlewaretoken': CSRFTOKEN, 'redirect': '/home/'}
postdata = urllib.parse.urlencode(post_form).encode()

Link(LOGIN_URL, CMS_URL, postdata).access()

# get dean url
temp_page = Link(TEMP_URL).access().ungzip()
soup = bs4.BeautifulSoup(temp_page, "html.parser")
redirect_url = soup.find('form')['action']
# print(redirect_url)

# get cookies
Link(redirect_url).access()
# cookie.save()

page = Link(RES_URL).access().ungzip()

# with open('origin.html', 'w', encoding='utf-8') as f:
#     f.write(page)

#-----------------------
#
# begin analysis page
#
#-----------------------

soup = bs4.BeautifulSoup(page, "html.parser")
myname = soup.find_all('strong')[0].string.strip()
table = soup.table
tr = [tr for tr in table if tr != '\n' and tr != table.contents[1]]
td_name = list()
td_credit = list()
td_span = list()
td_gp = list()
td_gpa = list()
td_grade = list()
exam_num = len(tr)
for td in tr:
    td_name.append(td.contents[7].string)
    td_credit.append(float(td.contents[11].string))
    td_span.append(td.contents[19])
# extract  grade from span
replace_html = list()
for item in td_span:
    spliter = item.contents[1]['data-content'].split()
    result = str()
    for text in spliter:
        if re.match('\d', text) or re.search('成绩', text):
            if re.match('最终', text):
                score = re.match(
                    '(最终成绩：)([A|B|C|D|E|F|P][+|-]?|[\d]{1,3})(.+)', text)
                this_grade = score.group(2)
                td_grade.append(this_grade)
                td_gp.append(grade_point(this_grade))
                score = '<p class=\"bg-danger\">' + this_grade + '</p>'
                text = '最终成绩：' + score + '<br/>'
            result = result + text
    replace_html.append(result)
# count gpa
gpa = 0
total_credits = 0
for i in range(0, exam_num):
    total_credits = total_credits + td_credit[i]
    gp = round(td_credit[i] * td_gp[i], 1)
    td_gpa.append(gp)
    gpa = gpa + gp
gpa = round(gpa / total_credits, 3)
# add gpa
merge = tuple(zip(td_credit, td_grade, td_gp, td_gpa))
# Result: key:name value:[学分 最终成绩 对应绩点 实绩点 ] //未使用
total = dict(zip(td_name, merge))

# prepare html
span = table.find_all('span')
count = 0
for sp in span:
    sp_td = sp.parent
    sp_td.clear()
    sp_td.append(replace_html[count])
    count = count + 1
new_tr = bs4.BeautifulSoup('<tr></tr>', "html.parser")
new_td_1 = new_tr.new_tag('td')
new_td_1.string = '总学分'
new_td_2 = new_tr.new_tag('td')
new_td_2.string = str(total_credits)
new_td_3 = new_tr.new_tag('td')
new_td_3.string = '您的绩点'
new_td_4 = new_tr.new_tag('td')
new_td_4.string = '<p class=\'bg-danger\'>' + str(gpa) + '</p>'
new_td_5 = new_tr.new_tag('td')
new_td_5.string = '计算公式'
new_td_6 = new_tr.new_tag('td')
new_td_6.string = '(课程学分1*绩点+课程学分2*绩点+课程学分n*绩点)/(课程学分1+课程学分2+课程学分n)'
new_tr.tr.append(new_td_1)
new_tr.tr.append(new_td_2)
new_tr.tr.append(new_td_3)
new_tr.tr.append(new_td_4)
new_tr.tr.append(new_td_5)
new_tr.tr.append(new_td_6)
table_wrapper = new_tr.new_tag('table')
table_wrapper['class'] = 'table table-bordered table-hover'
new_table = new_tr.tr.wrap(table_wrapper)

# write to file
with open('data.html', 'w', encoding='utf-8') as g:
    html_1 = table.prettify()
    html_2 = new_table.prettify()
    html = html_1 + html_2
    html = html.replace('&lt;', '<')
    html = html.replace('&gt;', '>')
    g.write(r"""<!DOCTYPE html>
<html lang="zh-CN">

<head>
    <title>""" + myname + r"""的成绩报告</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="stylesheet" href="bootstrap.min.css">
</head>

<body>
    <div class="container">
""" + html + r"""
        <div id="score">
        </div>
    </div>
    <script src='jquery.min.js'></script>
    <script src="bootstrap.min.js"></script>
    <script src="my.js"></script>
</body>

</html>""")
print('Done!')
input("Press any key to exit")
webbrowser.open('file://' + os.path.realpath('data.html'))

