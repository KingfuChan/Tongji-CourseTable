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
    # 使用str只能找到一个匹配项
    values = re.findall(r'value="(.*)"/>', res.content.decode('utf-8'))
    data = {
        'SAMLResponse': values[0],
        'RelayState': values[1],
    }
    res = session.post(assert_url, data)


def get_coursetable(session):
    print(session.cookies)
    url = "http://4m3.tongji.edu.cn/eams/courseTableForStd!courseTable.action"
    headers = {
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Origin': 'http://4m3.tongji.edu.cn',
        'Referer': 'http://4m3.tongji.edu.cn/eams/courseTableForStd!index.action',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest'
    }
    session.headers.update(headers)
    data = {
        'ignoreHead': '1',
        'setting.kind': 'std',
        'startWeek': '1',
        'semester.id': '108',
        'ids': '5836063678'  # 推测与用户挂钩，每个人对应不同的id
    }
    res = session.post(url, data)
    open("res_tmp.txt", 'w').write(res.content.decode('utf-8'))


if __name__ == "__main__":
    s = requests.Session()
    saml_login(s)
    get_coursetable(s)
