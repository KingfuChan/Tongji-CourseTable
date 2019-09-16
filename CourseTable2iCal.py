import re
from datetime import date, timedelta
import requests
from getpass import getpass
from bs4 import BeautifulSoup
from icalendar import Calendar, Event

semester_id = 108  # 2019学年第1学期，其他学期对应数值可在网页中元素审查得知
semester_start_date = date(2019, 9, 2)  # 开学日期2019.09.02


def generate_recurrence_rule(interval, day, lastdate):
    day_dict = {'星期一': 'MO', '星期二': 'TU', '星期三': 'WE',
                '星期四': 'TH', '星期五': 'FR', '星期六': 'SA', '星期日': 'SU', }
    freq = "FREQ=WEEKLY"
    until = lastdate.strftime("%Y%m%d")  # 最后一周结束
    until = f"UNTIL={until}T235959"
    interval = f"INTERVAL={interval}"
    byday = f"BYDAY={day_dict[day]}"
    return ';'.join((freq, until, interval, byday))


def proceed_courses(name, schedules):
    """
    返回一个包含课程名称、授课老师、上课地点、上下课时间（、重复规律）的字典，
    字典中字符串格式已调整至iCalendar RFC 5455规则，
    其中如果课程有重复，则上下课时间基于第一次课所在周数的星期一，通过重复规律BYDAY属性反映星期几上课。
    """
    info = schedules.rsplit(' ')
    teacher = info[0]
    day = info[1]
    time = info[2]
    week = info[3]
    place = info[4]

    course_dict = {  # 初始化将要返回的字典
        "name": name,
        "teacher": teacher,
        "place": place,
    }

    # 处理上课时间
    startdict = {  # 上课时间
        1: '080000', 2: '085000', 3: '100000', 4: '105000',
        5: '133000', 6: '142000', 7: '153000', 8: '162000',
        9: '175000', 10: '190000', 11: '195000', 12: '204000',
    }
    enddict = {  # 下课时间
        1: '084500', 2: '093500', 3: '104500', 4: '113500',
        5: '141500', 6: '150500', 7: '161500', 8: '170500',
        9: '183500', 10: '194500', 11: '203500', 12: '212500',
    }
    if '-' in time:  # 避免出现只有一节课的情况（未发现）
        classsindex = str(time).split('-')
        startclass = int(classsindex[0])
        endclass = int(classsindex[1])
    else:
        startclass = int(time)
        endclass = startclass
    starttime = startdict[startclass]
    endtime = enddict[endclass]

    # 处理周数信息，并转化iCalendar recurrence
    if not '-' in week:  # 只有某星期上课
        w = int(week.lstrip('[').rstrip(']'))
        firstdate = (timedelta(weeks=w-1) + semester_start_date
                     ).strftime("%Y%m%d")
    else:

        if '单'in week:
            startstop = week.lstrip('单[').rstrip(']').split('-')
            interval = 2
        elif '双' in week:
            startstop = week.lstrip('双[').rstrip(']').split('-')
            interval = 2
        else:  # 每周都上课
            startstop = week.lstrip('[').rstrip(']').split('-')
            interval = 1

        firstdate = (
            timedelta(weeks=int(startstop[0])-1) + semester_start_date).strftime("%Y%m%d")
        lastdate = timedelta(
            weeks=int(startstop[1])-1, days=6) + semester_start_date
        course_dict['RRULE'] = generate_recurrence_rule(
            interval, day, lastdate)

    course_dict['DTSTART'] = firstdate + 'T' + starttime
    course_dict['DTEND'] = firstdate + 'T' + endtime
    print(course_dict)
    return course_dict


def get_user_info():
    userid = input("请输入同济综合服务门户用户名>>>")
    password = getpass("请输入登录口令/密码。输入内容不显示，输入后请直接按回车键>>>")
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


def get_course_info(session, semester_id):
    """
    steps:
    1. Update headers   -> disguise for browser check
    2. POST index_url   -> get ids
    3. POST table_url   -> get course table
    return a beautifulsoup object
    """
    print("正在获取课表信息...")

    # 1. Update headers   -> disguise for browser check
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
        'semester.id': semester_id,
        'ids': ids,
    }
    res = session.post(table_url, data=data)
    soup = BeautifulSoup(res.content, "html.parser")
    table_html = soup.prettify(encoding='utf-8')
    open("test.html", 'wb').write(table_html)  # 用于调试
    print("课表信息已获取！")
    return table_html


def convert_to_ical(html):
    soup = BeautifulSoup(html, "html.parser")
    courses = soup.find('tbody').find_all('tr')
    for r in courses:
        cells = r.find_all('td')
        name = re.sub(r'[①②③④⑤⑥⑦\s]', '', cells[2].get_text())  # 去掉精品课程标识
        schedules = list(
            filter(None, [l.strip() for l in cells[8].get_text().strip().splitlines()]))
        for s in schedules:
            proceed_courses(name, s)


def main():
    #session = requests.Session()
    #login(session, "http://4m3.tongji.edu.cn/eams/samlCheck")
    #courses = get_course_info(session, semester_id)
    # convert_to_ical(courses)
    convert_to_ical(open("test.html", 'r', encoding='utf-8').read())
    # _pause = input("按回车键退出！")


if __name__ == "__main__":
    main()
