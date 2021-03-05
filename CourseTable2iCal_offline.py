"""
Tongji-CourseTable
————获取同济大学课程表并编写为iCalendar文件（离线版）

实现思路：
1、通过网页开发者工具或抓包软件手工获取课程表json文件，
   请求URL为：https://1.tongji.edu.cn/api/electionservice/reportManagement/findStudentTimetab
2、将课程表转换为iCalendar格式。
用到的第三方库：icalendar，运行前请先使用pip安装。

https://github.com/KingfuChan/Tongji-CourseTable
"""


import json
from datetime import datetime, timedelta

# 以下为第三方库
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


def get_course_info():
    mod_str = input("请输入开学日期（周一），格式为 年-月-日>")
    begin_date = datetime.strptime(mod_str, r"%Y-%m-%d")

    filename = input("请输入课程表json文件名>")

    # 函数返回
    rt = {
        "BeginDate": begin_date,
        # a list containing all classes
        "Courses": json.load(open(filename, encoding='utf-8'))["data"],
    }
    return rt


def process_course(course):
    """提取某课程所有信息，按照weeks列表逐一生成Event对象并返回"""
    if course["timeTableList"] == None:
        return  # TODO:如为None则为实践类课程？

    rt = []
    description = "课号：{}\n课程授课教师：{}\n本次课授课教师：{}\n学分：{}\n考试/查：{}\n备注：{}"

    for timetable in course["timeTableList"]:

        dscr = description.format(course["classCode"],
                                  course["teacherName"],
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
    try:
        if step == 0:
            courses = get_course_info()
            step += 1
        if step == 1:
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
