# encoding: utf-8
'''
@author: depchen

@file: zhihu_login_requests.py

@time: 2017/11/22 16:46

@desc:
'''

import requests
try:
    import cookielib
except:
    import http.cookiejar as cookielib

import re

session=requests.session()
session.cookies=cookielib.LWPCookieJar(filename="cookies.txt")
try:
    session.cookies.load(ignore_discard=True)
except:
    print("cookie未能加载")

agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36"
header={
    "HOST":"www.zhihu.com",
    "Referer":"https://www.zhihu.com",
    "User-Agent":agent
}


def get_xsrf():
    response=requests.get("https://www.zhihu.com/#signin",headers=header)
    response_text=response.text
    match_obj=re.match('.*name="_xsrf" value="(.*?)"',response_text,re.S)
    if match_obj:
        match_obj=match_obj.group(1)
        return (match_obj)
    else:
        return ""


def get_index():
    response = session.get("https://www.zhihu.com", headers=header)
    with open("index_page.html","wb") as f:
        f.write(response.text.encode("utf-8"))
    print("ok")


def is_login():
    #通过个人中心页面返回状态码来判断是否为登录
    inbox_url="https://www.zhihu.com/inbox"
    response=session.get(inbox_url,headers=header,allow_redirects=False)
    if response.status_code!=200:
        return False
    else:
        return True
    pass


def get_captcha():
    import time
    t=str(int(time.time()*1000))
    captcha_url="https://www.zhihu.com/captcha.gif?r={0}&type=login".format(t)
    t=session.get(captcha_url,headers=header)
    with open("captcha.jpg","wb") as f:
        f.write(t.content)
        f.close()

    from PIL import Image
    try:
        im=Image.open('captcha.jpg')
        im.show()
        im.close()
    except:
        pass

    captcha=input("输入验证码\n>")
    return captcha



def zhihu_login(account,password):
    #知乎登录
    if re.match("^1\d{10}",account):
        print("手机登录")
        post_url="https://www.zhihu.com/login/phone_num"
        post_data={
            "_xsrf":get_xsrf(),
            "phone_num":account,
            "password":password,
            "captcha":get_captcha()
        }
    else:
        if "@" in account:
            print("邮箱登录")
            post_url = "https://www.zhihu.com/login/email"
            post_data = {
                "_xsrf": get_xsrf(),
                "phone_num": account,
                "password": password
            }
    response_text = session.post(post_url, data=post_data, headers=header)
    session.cookies.save()


zhihu_login("18119318127","wei915421")
# get_index()
is_login()
#get_captcha()