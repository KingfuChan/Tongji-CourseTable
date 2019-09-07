import urllib
from http import cookiejar

idsurl = "https://ids.tongji.edu.cn:8443/nidp/saml2/sso?id=3423&sid=0&option=credential&sid=0"
loginurl = "https://ids.tongji.edu.cn:8443/nidp/saml2/sso?sid=0&sid=0"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'}

userid = '1851175'
userpw = 'CjfEki0420'
params = {
    'option': 'credential',
    'Ecom_User_ID': userid,
    'Ecom_Password': userpw,
    'Txtidcode': '0000'}
data = bytes(urllib.parse.urlencode(params), encoding='utf-8')

cj = cookiejar.LWPCookieJar()
cookie_support = urllib.request.HTTPCookieProcessor(cj)
opener = urllib.request.build_opener(
    cookie_support, urllib.request.HTTPHandler)
urllib.request.install_opener(opener)
loginopen = urllib.request.urlopen(loginurl, data=data)

with open('request.html', 'w', encoding='utf-8') as f:
    f.write(loginopen.read().decode('utf-8'))

with open('cookie.txt', 'w', encoding='utf-8') as c:
    for j in cj:
        c.write(f"{j.name} = {j.value}\n")
