import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# 考虑直接post http://4m3.tongji.edu.cn/eams/courseTableForStd!courseTable.action


class ClassObject(object):

    def __init__(self, *argv):
        """六个参数：课程名称、授课老师，星期几，第几节课，上课周数，上课地点。"""
        self.name, self.teacher, self.day, self.time, self.week, self.place = argv

        # 处理周数信息
        week = str(self.week)
        if not '-' in week:  # 排除只有某星期上课
            week = (week, week)

        if '单' in week:  # 分辨单双周课
            self.oddeven = 'odd'
            week = week.lstrip('单[').rstrip(']').split('-')
        elif '双' in week:
            self.oddeven = 'even'
            week = week.lstrip('双[').rstrip(']').split('-')
        else:
            self.oddeven = 'all'
            week = week.lstrip('[').rstrip(']').split('-')
        start, end = week
        self.start_week = int(start)
        self.end_week = int(end)

    def format_to_ics(self):
        print(self.name, self.start_week, self.end_week)


class CourseObject(object):

    def __init__(self, row):
        # 区分列表与索引编号
        self.name = str(row.find_elements_by_tag_name("td")[2].text)
        self.schedule = str(row.find_elements_by_tag_name("td")[8].text)

    def parse_info(self):
        info = self.schedule
        lines = info.splitlines()
        classes = []
        for il in lines:
            infolist = il.rsplit(' ')
            infolist.extend(['']*4)
            teacher = infolist[0]
            day = infolist[1]
            time = infolist[2]
            week = infolist[3]
            place = infolist[4]
            classes.append(ClassObject(
                self.name, teacher, day, time, week, place))
        return classes


def get_classes(user_id, user_password):
    opt = Options()
    # opt.add_argument('--headless')
    browser = webdriver.Chrome(
        executable_path="chromedriver.exe", chrome_options=opt)
    browser.get("http://4m3.tongji.edu.cn/")  # 打开无界面Chrome

    username = browser.find_element_by_id("username")
    username.send_keys(user_id)

    password = browser.find_element_by_id("password")
    password.send_keys(user_password)

    captcha = browser.find_element_by_id("ehong-code").text  # 获取验证码
    txtidcode = browser.find_element_by_id("Txtidcode")  # 验证码输入框
    txtidcode.send_keys(captcha)

    submit = browser.find_element_by_name("btsubmit")
    submit.click()  # 按登录键
    browser.implicitly_wait(5)

    mycurriculum = browser.find_element_by_link_text("我的课程")
    mycurriculum.click()
    browser.implicitly_wait(1)
    schedule = browser.find_element_by_link_text("我的课表")  # 点击打开课表
    schedule.click()
    browser.implicitly_wait(5)
    # time.sleep(2)  # 等待课表加载完成

    # 切换课表
    cal_bar = browser.find_element_by_class_name("calendar-text")
    cal_bar.click()
    cal_yeartb = browser.find_element_by_id("semesterCalendar_yearTb")
    cal_semetb = browser.find_element_by_id("semesterCalendar_termTb")
    # 3行4列，2018-2019
    cal_year = cal_yeartb.find_elements_by_tag_name('tr')[3]
    cal_year = cal_year.find_elements_by_tag_name('td')[0]
    cal_year.click()
    # 1行1列，1学期
    cal_seme = cal_semetb.find_elements_by_tag_name('tr')[0]
    cal_seme = cal_seme.find_elements_by_tag_name('td')[0]
    cal_seme.click()
    cal_switch = browser.find_element_by_xpath(
        "/html/body/table[@id='mainTable']/tbody/tr/td[@id='rightTD']/div/div[2]/form/div[2]/input[@value='切换学期']")
    cal_switch.click()
    browser.implicitly_wait(5)
    # time.sleep(2)  # 等待课表加载完成

    # 读取课表内容
    schedule_table = browser.find_element_by_class_name('grid').find_element_by_tag_name(
        'table').find_element_by_tag_name('tbody').find_elements_by_tag_name('tr')  # 不知道为什么出错
    allclasses = []
    for st in schedule_table:
        c = CourseObject(st)
        allclasses.extend(c.parse_info())
    # allclasses包含了所有单节课的信息，为ClassObject组成的列表

    browser.save_screenshot('screenshot.png')
    browser.quit()

    return allclasses


def make_ics_file():
    pass


if __name__ == "__main__":
    user_id = input("Please enter your ID.>")
    user_pw = input("Please enter your password.>")
    classes = get_classes(user_id, user_pw)
    for cl in classes:
        cl.format_to_ics()
