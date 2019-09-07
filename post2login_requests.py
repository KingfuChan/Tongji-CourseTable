import requests

data = {
    "Ecom_User_ID": '1851175',
    "Ecom_Password": 'CjfEki0420',
    "Txtidcode": ''
}
r = requests.get(
    "https://ids.tongji.edu.cn:8443/nidp/saml2/sso")
with open('p2lrs.html', 'w', encoding=r.encoding) as f:
    f.write(r.text)
