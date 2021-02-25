"""
Tongji-CourseTable
————获取同济大学课程表并编写为iCalendar文件

实现思路：
1、登录并从1.tongji.edu.cn获取课程表
2、将课程表转换为iCalendar格式。
用到的第三方库：requests, beautifulsoup4，icalendar，运行前请先使用pip安装。
iCalendar文件导入手机或电脑的方法请参考 https://i.scnu.edu.cn/ical/doc

https://github.com/KingfuChan/Tongji-CourseTable
"""


import re
import json
from datetime import datetime, timedelta
from getpass import getpass
import base64

# 以下为第三方库
import requests
from bs4 import BeautifulSoup
from icalendar import Calendar, Event, vRecur


# 上下课时间列表
CLASS_START_TIME = {  # 上课时间（时，分）
    1: (8, 0), 2: (8, 50), 3: (10, 0), 4: (10, 50),
    5: (13, 30), 6: (14, 20), 7: (15, 30), 8: (16, 20),
    9: (17, 50), 10: (19, 00), 11: (19, 50), 12: (20, 40),
}
CLASS_END_TIME = {  # 下课时间（时，分）
    1: (8, 45), 2: (9, 35), 3: (10, 45), 4: (11, 35),
    5: (14, 15), 6: (15, 5), 7: (16, 15), 8: (17, 5),
    9: (18, 35), 10: (19, 45), 11: (20, 35), 12: (21, 25),
}


def get_user_info():
    userid = input("请输入同济综合服务门户用户名（学号）>")
    password = getpass("请输入登录口令/密码。输入内容不显示，输入后请直接按回车键>")
    idcode = input("请输入验证码，图片位于imgCode.jpg中>")
    return userid, password, idcode


def login(session, init_url):
    """
    步骤：
    1. 由1.tongji.edu.cn进行两次重定向
    2. 获得登录链接
    3. 获得登录网页及验证码图片
    4. 提交登录信息
    5. 由返回内容判断是否登录成功，如成功返回ids跳转链接
    """

    # 1
    print("正在连接到1.tongji.edu.cn...")
    res = session.get(init_url, allow_redirects=False)
    rd1_url = res.headers["location"]
    res = session.get(rd1_url, allow_redirects=False)
    rd2_url = res.headers["location"]

    # 2
    res = session.get(rd2_url)
    soup = BeautifulSoup(res.content, "html.parser")
    base_url = "https://ids.tongji.edu.cn:8443"
    sid_url = base_url + soup.find('form')['action']

    # 3
    res = session.post(sid_url)
    img_url = "https://ids.tongji.edu.cn:8443/nidp/app/login?sid=0&sid=0&flag=true"
    res = session.get(img_url)
    imgstr = str(res.text).replace("data:image/jpg;base64,", "")
    open('imgCode.jpg', 'wb').write(base64.b64decode(imgstr))

    # 4
    userid, password, idcode = get_user_info()
    login_data = {
        'option': 'credential',
        'Ecom_User_ID': userid,
        'Ecom_Password': password,
        'Ecom_code': idcode,
    }
    print("登录中...")
    res = session.post(sid_url, data=login_data)

    # 5
    if rd1_url not in str(res.content):
        raise KeyError("登录失败！请检查账号信息及验证码。")
    else:
        print("登录成功！")
        return rd1_url


def get_course_info(session, init_url):
    """
    1.tongji采用json储存课表信息
    步骤：（init_url为登录时的第一个重定向链接，即为登录函数返回值）
    1. 使用两次重定向获取cookies
    2. 获取学期信息（学期id）
    3. 获取该学期课表
    """

    # 重定向
    res = session.get(init_url, allow_redirects=False)
    re1_url = res.headers["location"]
    res = session.get(re1_url, allow_redirects=False)
    re2_url = res.headers["location"]

    # 解析第二次重定向中的登录信息
    uid = re.findall(r"uid=([0-9]*)", re2_url)[0]
    token = re.findall(r"token=([a-z0-9]*)", re2_url)[0]
    ts = re.findall(r"ts=([0-9]*)", re2_url)[0]
    pdata = {
        "uid": uid,
        "token": token,
        "ts": ts,
    }
    rlg_url = "https://1.tongji.edu.cn/api/sessionservice/session/login"
    session.post(rlg_url, pdata)

    # 获取学期id
    cal_url = "https://1.tongji.edu.cn/api/baseresservice/schoolCalendar/currentTermCalendar"
    res = session.get(cal_url)
    cal_curr = json.loads(res.content)
    cur_id = cal_curr["data"]["schoolCalendar"]['id']
    mod_req = input(f"{cal_curr['data']['name']}，id为：{cur_id}，是否更改？(y/n)")
    if mod_req.lower() == 'y':
        cur_id = int(input("请输入学期id>"))

    cal_list_url = "https://1.tongji.edu.cn/api/baseresservice/schoolCalendar/list"
    res = session.get(cal_list_url)
    cal_list = json.loads(res.content)
    semes_list = list(cal_list["data"])
    for s in semes_list:
        if s['id'] == cur_id:
            begin_date = datetime.fromtimestamp(s["beginDay"]/1000)
            break
    bgd_str = begin_date.strftime(r"%Y-%m-%d")
    mod_req = input(f"开学日期{bgd_str}，是否修改？(y/n)>")
    if mod_req.lower() == 'y':
        mod_str = input("请输入日期，格式为 年-月-日>")
        begin_date = datetime.strptime(mod_str, r"%Y-%m-%d")

    # 获取课表json
    table_url = "https://1.tongji.edu.cn/api/electionservice/reportManagement/findStudentTimetab?calendarId={}"
    res = session.get(table_url.format(cur_id, uid))

    # 函数返回
    rt = {
        "BeginDate": begin_date,
        # a list containing all classes
        "Courses": json.loads(res.content)["data"],
    }
    return rt


# 以上为1.tongji相关，以下为日历相关


def process_course(course):
    """提取某课程所有信息，按照weeks列表逐一生成Event对象并返回"""
    if course["timeTableList"] == None:
        return  # TODO:如为None则为实践类课程？

    rt = []
    description = "课号：{}\n授课教师：{}\n学分：{}\n考试/查：{}\n备注：{}"

    for timetable in course["timeTableList"]:

        dscr = description.format(course["classCode"],
                                  timetable["teacherName"],
                                  course["credits"],
                                  course["assessmentModeI18n"],
                                  course["remark"],
                                  )
        room = ' '.join(filter(None, list((timetable["campusI18n"],
                                           timetable["roomIdI18n"],
                                           timetable["roomLable"]))))

        day = timetable["dayOfWeek"]
        weeks = timetable["weeks"]
        h, m = CLASS_START_TIME[timetable["timeStart"]]
        starttime = timedelta(hours=h, minutes=m)
        h, m = CLASS_END_TIME[timetable["timeEnd"]]
        endtime = timedelta(hours=h, minutes=m)

        for w in weeks:
            ev = Event()
            ev.add("SUMMARY", timetable["courseName"])
            ev.add("LOCATION", room)
            ev.add("DESCRIPTION", dscr)
            # 星期与日期均需减一
            class_date = seme_start_date + timedelta(weeks=w-1, days=day-1)
            ev.add("DTSTART", class_date + starttime)
            ev.add("DTEND", class_date + endtime)
            rt.append(ev)

    return rt


def make_ics(course_dict):
    cal = Calendar()
    cal.add('version', 3.0)
    global seme_start_date
    seme_start_date = course_dict["BeginDate"]

    event_whole = []
    for c in course_dict["Courses"]:
        event_whole.extend(process_course(c))

    for e in event_whole:
        cal.add_component(e)

    filename = input("请输入保存的文件名>")
    with open(f'{filename}.ics', 'wb') as ics:
        ics.write(cal.to_ical())
    print(f"iCalendar日历文件已导出到{filename}.ics中！")


# 主函数
def main(step=0):
    global session, login_url  # 保留按步骤重试的会话
    tj1_url = "https://1.tongji.edu.cn/api/ssoservice/system/loginIn"
    try:
        if step == 0:
            session = requests.Session()
            session.headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36 Edg/88.0.705.74",
            }
            login_url = login(session, tj1_url)
            step += 1
        if step == 1:
            courses = get_course_info(session, login_url)
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
