import re
import requests
from bs4 import BeautifulSoup


def get_user_info():
    userid = input("请输入同济综合服务门户用户名\t>>>")
    password = input("请输入登录口令（密码）\t\t>>>")
    return userid, password


def login(session, init_url):
    """
    steps:
    1. GET init_url     -> forward to sso_url
    2. GET sso_url      -> get sid_url
    3. POST sid_url     -> submit login data
    4. POST sid_url     -> get assert_url and assert_data
    5. POST assert_url  -> redirect to init_url, login OK!
    """

    # 1. GET init_url     -> forward to sso_url
    print("登录前准备...")
    res = session.get(init_url)
    soup = BeautifulSoup(res.content, "html.parser")
    sso_url = soup.find('meta')['content'][6:]

    # 2. GET sso_url      -> get sid_url
    base_url = "https://ids.tongji.edu.cn:8443"
    res = session.get(sso_url)
    soup = BeautifulSoup(res.content, "html.parser")
    sid_url = base_url + soup.find('form')['action'].replace('amp', '')

    # 3. POST sid_url     -> submit login data
    userid, password = get_user_info()
    print("登录中...")
    login_data = {
        'Ecom_Password': password,
        'Ecom_User_ID': userid,
        'option': 'credential',
        'submit': '登录',
    }
    res = session.post(sid_url, data=login_data)

    # 4. POST sid_url     -> get assert_url and assert_data
    res = session.get(sid_url)
    soup = BeautifulSoup(res.content, "html.parser")
    assert_url = soup.find("form")["action"]
    values = [t['value'] for t in soup.find_all("input")]
    assert_data = {
        'SAMLResponse': values[0],
        'RelayState': values[1],
    }

    # 5. POST assert_url  -> redirect to init_url, login OK!
    res = session.post(assert_url, data=assert_data)
    soup = BeautifulSoup(res.content, "html.parser")
    print("登录成功！")


def get_course_info(session):
    """
    steps:
    1. Update headers   -> overpass client check
    2. POST index_url   -> get ids
    3. POST table_url   -> get course table
    """
    print("正在获取课表信息...")

    # 1. Update headers   -> overpass client check
    index_url = "http://4m3.tongji.edu.cn/eams/courseTableForStd!index.action"
    table_url = "http://4m3.tongji.edu.cn/eams/courseTableForStd!courseTable.action"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36'}
    session.headers.update(headers)

    # 2. POST index_url   -> get ids
    res = session.post(index_url)
    soup = BeautifulSoup(res.content, "html.parser")
    script = soup.find("script", language="JavaScript").get_text()
    ids = re.findall(r'"ids","([0-9]*)"', script)[0]

    # 3. POST table_url   -> get course table
    data = {
        'ignoreHead': '1',
        'setting.kind': 'std',
        'startWeek': '1',
        'semester.id': '108',  # 2019学年第1学期，其他学期对应数值可在网页中元素审查得知
        'ids': ids,
    }
    res = session.post(table_url, data=data)
    soup = BeautifulSoup(res.content, "html.parser")
    open("test.html", 'wb').write(soup.prettify(
        encoding=soup.original_encoding))  # 用于调试
    print("课表信息已获取！")
    _pause = input("按回车键退出！")


def convert_to_ical(html):
    pass


def main():
    session = requests.Session()
    login(session, "http://4m3.tongji.edu.cn/eams/samlCheck")
    courses = get_course_info(session)
    convert_to_ical(courses)


if __name__ == "__main__":
    main()
