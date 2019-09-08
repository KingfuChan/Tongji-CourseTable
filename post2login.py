import re
import requests


def input_info():
    userid = input("Enter ID:")
    userpw = input("Enter Password:")
    return userid, userpw


def saml_login(session):
    """
    step:
    1. GET init_url    -> forward to sso_url
    2. GET sso_url     -> get a form and get sid_url
    3. POST sid_url    -> get login_url
    4. POST login_url  -> submit login data
    5. GET sid_url     -> get aseert_url
    5. POST assert_url -> 302 and then OK!
    """
    # 1
    base_url = 'https://ids.tongji.edu.cn:8443'
    init_url = 'http://4m3.tongji.edu.cn/eams/samlCheck'
    res = session.get(init_url)

    # 2
    sso_url = re.findall(r'url=(.*)"><', str(res.content))[0]
    res = session.get(sso_url)

    # 3
    sid_url = base_url + re.findall(r'action="(.*)"><', str(res.content))[0]
    res = session.post(sid_url)

    # 4
    login_url = sid_url
    username, password = input_info()
    data = {
        'Ecom_Password': password,
        'Ecom_User_ID': username,
        'option': 'credential',
        'submit': '登录'
    }
    res = session.post(login_url, data)

    # 5
    sid_url = re.findall(r"top.location.href=\\'(.*)\\';", str(res.content))[0]
    res = session.get(sid_url)

    # 6
    assert_url = "http://4m3.tongji.edu.cn/eams/saml/SAMLAssertionConsumer"
    data = {
        'SAMLResponse': re.findall(r'value="(.*)"/>', str(res.content))[0]
    }
    res = session.post(assert_url, data)


def get_coursetable(session):
    url = "http://4m3.tongji.edu.cn/eams/courseTableForStd!courseTable.action"
    data = {
        'ignoreHead': '1',
        'setting.kind': 'std',
        'startWeek': '1',
        'semester.id': '108',
        'ids': '5836063678'  # 推测与用户挂钩，每个人对应不同的id
    }
    res = session.post(url, data)
    open('res_temp.html', 'w').write(str(res.content))


if __name__ == "__main__":
    s = requests.Session()
    saml_login(s)
    get_coursetable(s)
