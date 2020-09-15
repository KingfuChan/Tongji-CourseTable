# Tongji-CourseTable
获取同济大学课程表并编写为iCalendar文件

工程背景：

某些课表app过于臃肿，附加功能过多。随着手机系统完善，日历应用越来越美观实用。本工程用于抓取同济大学本研一体化平台中的课程表信息并转换为iCalendar格式供导入手机或电脑系统（Android, iOS, Windows, MacOS均可）。

工程思路：

~~1、模拟登录4m3.tongji.edu.cn并抓取课程表。~~

1、登录1.tongji.edu.cn，并请求课表。

2、将课程表转换为iCalendar格式。

用到的第三方库：requests, beautifulsoup4，icalendar，运行前请先使用pip安装。

~~iCalendar文件导入手机或电脑的方法请参考 https://i.scnu.edu.cn/ical/doc~~ （华工这个链接失效了，自己找教程吧……）


2020.9.15更新：

由于4m3即将停止使用，本脚本对1.tongji进行了适配，请下载CourseTable2iCal_1.py运行，原先不带_1的文件运行会出错，仅保留在此作学习参考用。

另外由于1.tongji使用了新的课表展示/储存方式，因此iCalendar文件不再写成recurrence的规则，后果就是不能单独修改某个日程然后把剩余的都一并修改。

顺便吐槽一下，1.tongji有的bug让我感觉难以接受 :(