from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import requests


def get_cookies(user_id, user_password):
    opt = Options()
    opt.add_argument('--headless')
    browser = webdriver.Chrome(
        executable_path="chromedriver.exe", chrome_options=opt)
    # 打开无界面Chrome
    browser.get("http://4m3.tongji.edu.cn/eams/samlCheck")

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
    cookies = browser.get_cookie('JSESSIONID')['value']
    browser.quit()
    return str(cookies).rsplit('.')


if __name__ == "__main__":
    JSID, server = get_cookies('', '')  # 填写账号密码
    url = "http://4m3.tongji.edu.cn/eams/courseTableForStd!courseTable.action"
    headers = {
        'Accept': '*/*',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Cookie': f"semester.id=107; JSESSIONID={JSID}.{server}; SERVERNAME=s{server}; oiosaml-fragment=",
        'Origin': 'http://4m3.tongji.edu.cn',
        'Referer': 'http://4m3.tongji.edu.cn/eams/courseTableForStd!index.action',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest'
    }
    data = {
        'ignoreHead': '1',
        'setting.kind': 'std',
        'startWeek': '1',
        'semester.id': '106',
        'ids': '5836063678'  # 推测与用户挂钩，每个人对应不同的id
    }
    req = requests.post(url, data=data, headers=headers, verify=False)
    with open('s+r.html', 'w', encoding=req.encoding) as f:
        f.write(req.text)
