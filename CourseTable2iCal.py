"""
Tongji-CourseTable
————获取同济大学课程表并编写为iCalendar文件

工程思路：
1、模拟登录4m3.tongji.edu.cn并抓取课程表。
2、将课程表转换为iCalendar格式。
用到的第三方库：requests, beautifulsoup4，icalendar，运行前请先使用pip安装。
iCalendar文件导入手机或电脑的方法请参考 https://i.scnu.edu.cn/ical/doc

https://github.com/KingfuChan/Tongji-CourseTable
"""


import re
from datetime import datetime, timedelta
from getpass import getpass
# 以下为第三方库
import requests
from bs4 import BeautifulSoup
from icalendar import Calendar, Event, vRecur


"""！！！变更学期后此处需更改！！！"""
semester_id = 109  # 2019学年第2学期，其他学期对应数值可在网页中元素审查得知
semester_start_date = datetime(2020, 2, 17)  # 开学日期2020年2月17日星期一
"""！！！变更学期后此处需更改！！！"""

# 星期几对照字典
day_dict_num = {'星期一': 1, '星期二': 2, '星期三': 3,  # 用于timedelta
                '星期四': 4, '星期五': 5, '星期六': 6, '星期日': 7, }


def get_user_info():
    userid = input("请输入同济综合服务门户用户名（学号）>")
    password = getpass("请输入登录口令/密码。输入内容不显示，输入后请直接按回车键>")
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
    print("正在连接到4m3.tongji.edu.cn...")
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
    print("课表信息已获取！")
    return table_html


# 以上为4m3相关，以下为日历相关


def generate_recurrence_rule(interval, lastdate):
    until = lastdate + timedelta(hours=23, minutes=59, seconds=59)  # 最后一周结束
    return vRecur(freq="WEEKLY", until=until, interval=interval)


def generate_ical_event(class_dict):
    event = Event()
    event.add('SUMMARY', class_dict['name'])
    event.add('DTSTART', class_dict['DTSTART'])
    event.add('DTEND', class_dict['DTEND'])

    if 'RRULE' in class_dict.keys():
        event.add('RRULE', class_dict['RRULE'])

    event.add('LOCATION', class_dict['place'])
    description = f"授课教师：{class_dict['teacher']}"
    event.add('description', description)
    return event


def process_classes(name, schedules):
    """
    返回一个包含课程名称、授课老师、上课地点、上下课时间（、重复规律）的字典，
    所有日期和时间都为python datetime库的datetime对象，
    其中如果课程有重复，则上下课时间基于第一次课所在周数的星期一，通过重复规律BYDAY属性反映星期几上课。
    """
    info = schedules.rsplit(' ')
    teacher = info[0]
    day = info[1]
    classindex = info[2]
    week = info[3]
    place = info[4]

    class_dict = {  # 初始化将要返回的字典
        "name": name,
        "teacher": teacher,
        "place": place,
    }

    # 处理上课时间
    startdict = {  # 上课时间（时，分）
        1: (8, 0), 2: (8, 50), 3: (10, 0), 4: (10, 50),
        5: (13, 30), 6: (14, 20), 7: (15, 30), 8: (16, 20),
        9: (17, 50), 10: (19, 00), 11: (19, 50), 12: (20, 40),
    }
    enddict = {  # 下课时间（时，分）
        1: (8, 45), 2: (9, 35), 3: (10, 45), 4: (11, 35),
        5: (14, 15), 6: (15, 5), 7: (16, 15), 8: (17, 5),
        9: (18, 35), 10: (19, 45), 11: (20, 35), 12: (21, 25),
    }
    if '-' in classindex:
        classsindex = str(classindex).split('-')
        startclass = int(classsindex[0])
        endclass = int(classsindex[1])
    else:  # 避免出现只有一节课的情况（未发现）
        startclass = int(classindex)
        endclass = startclass
    h, m = startdict[startclass]
    starttime = timedelta(hours=h, minutes=m)
    h, m = enddict[endclass]
    endtime = timedelta(hours=h, minutes=m)

    # 处理周数信息，并转化iCalendar recurrence
    if not '-' in week:  # 只有某星期上课
        w = int(week.lstrip('[').rstrip(']'))
        firstdate = timedelta(
            weeks=w-1, days=day_dict_num[day]-1) + semester_start_date
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

        firstdate = timedelta(
            weeks=int(startstop[0])-1, days=day_dict_num[day]-1) + semester_start_date
        lastdate = timedelta(
            weeks=int(startstop[1])-1, days=day_dict_num[day]-1) + semester_start_date
        class_dict['RRULE'] = generate_recurrence_rule(interval, lastdate)

    class_dict['DTSTART'] = firstdate + starttime
    class_dict['DTEND'] = firstdate + endtime
    return class_dict


def make_ics(html):
    cal = Calendar()
    cal.add('version', 2.0)

    soup = BeautifulSoup(html, "html.parser")
    courses = soup.find('tbody').find_all('tr')
    for r in courses:
        cells = r.find_all('td')
        name = re.sub(r'[①②③④⑤⑥⑦\s]', '', cells[2].get_text())  # 去掉精品课程标识
        schedules = list(
            filter(None, [l.strip() for l in cells[8].get_text().strip().splitlines()]))
        for s in schedules:
            classdict = process_classes(name, s)
            cal.add_component(generate_ical_event(classdict))

    filename = input("请输入保存的文件名>")
    with open(f'{filename}.ics', 'wb') as ics:
        ics.write(cal.to_ical())
    print(f"iCalendar日历文件已导出到{filename}.ics中！")


# 主函数
def main(step=0):
    global session  # 保留按步骤重试的会话
    try:
        if step == 0:
            session = requests.Session()
            login(session, "http://4m3.tongji.edu.cn/eams/samlCheck")
            step += 1
        if step == 1:
            courses = get_course_info(session, semester_id)
            step += 1
        if step == 2:
            make_ics(courses)
            step += 1
    except Exception as err:
        print("发生错误：\n"+repr(err))
        retry = input("是否重试？(y/n)>")
        if retry.lower() == 'y':
            return main(step)
        else:
            return step
    else:
        _pause = input("按回车键退出！")
        return step


if __name__ == "__main__":
    main()
