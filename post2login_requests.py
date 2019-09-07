import requests

data = {
    "Ecom_User_ID": '',  # 待填
    "Ecom_Password": '',
    "Txtidcode": ''
}
r = requests.get(
    "https://ids.tongji.edu.cn:8443/nidp/saml2/sso")
with open('p2lrs.html', 'w', encoding=r.encoding) as f:
    f.write(r.text)
