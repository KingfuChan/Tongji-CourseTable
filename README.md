# Tongji-CourseTable
获取同济大学课程表并编写为iCalendar文件

课题背景：某些课表app过于臃肿，附加功能过多。随着手机系统完善，日历应用越来越美观实在，故希望抓取同济大学本研一体化平台中的课程表信息并转换为iCalendar格式供导入。

工程思路：

1、requests库模拟登录4m3.tongji.edu.cn并抓取课程表

2、将课程表转换为iCalendar格式。（未实现）

用到的第三方库：requests, beautifulsoup4