## 代码块1
import win32serviceutil
import win32service
import win32event
import servicemanager
import socket
import os
import sys
import logging
import inspect
import time


import threading
from smtplib import SMTP_SSL
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header

from urllib.request import urlopen
import logging

# smtplib模块主要负责发送邮件：是一个发送邮件的动作，连接邮箱服务器，登录邮箱，发送邮件（有发件人，收信人，邮件内容）。
# email模块主要负责构造邮件：指的是邮箱页面显示的一些构造，如发件人，收件人，主题，正文，附件等。
current_ip = urlopen('http://icanhazip.com', timeout=5).read()
current_ip = current_ip.decode(encoding='utf-8')
sender_qq = "xxxxxxxxx@163.com"  # 发送邮箱
receiver = 'xxxxxx@qq.com'  # 接收邮箱
pwd = "xxxxxxxxxx"  # 授权码

base_dir = os.path.dirname(os.path.abspath(__file__))
log_base_dir = os.path.join(base_dir, "logs")
file_name = os.path.join(log_base_dir, "ip.txt")
log_name = os.path.join(log_base_dir, "get_ip.log")

if not os.path.exists(log_base_dir):
    os.mkdir(log_base_dir)

logger = logging.getLogger('logger')
logger.setLevel(level=logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')

file_handler = logging.FileHandler(log_name, 'a+', encoding='utf-8')
file_handler.setLevel(level=logging.INFO)
file_handler.setFormatter(formatter)

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.DEBUG)
stream_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(stream_handler)

# 服务名称
svc_name = 'MyService'

# 服务显示名称
svc_display_name = 'The Service'

# 服务描述
svc_description = '获取外网IP发送到邮箱.'



class MyService(win32serviceutil.ServiceFramework):
    _svc_name_ = svc_name
    _svc_display_name_ = svc_display_name
    _svc_description_ = svc_description

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        socket.setdefaulttimeout(60)
        self.is_running = True

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        self.is_running = False

    def SvcDoRun(self):
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                              servicemanager.PYS_SERVICE_STARTED,
                              (self._svc_name_, ''))
        self.main()

        # 发送邮件
    def send_email(self,my_ip):
        host_server = 'smtp.163.com'  # qq邮箱smtp服务器
        mail_title = 'IP更换提醒-python'  # 邮件标题
        # mail_content = "外网IP：{}\n发送时间：{}".format(my_ip, time)  # 邮件正文内容
        mail_content = "外网IP：{}".format(my_ip)  # 邮件正文内容
        # 初始化一个邮件主体
        msg = MIMEMultipart()
        msg["Subject"] = Header(mail_title, 'utf-8')
        #msg["From"] = Header(sender_qq, 'utf-8')
        # msg["To"] = Header("测试邮箱",'utf-8')
        msg['To'] = Header(receiver, 'utf-8')
        # 邮件正文内容
        msg.attach(MIMEText(mail_content, 'plain', 'utf-8'))
        smtp = SMTP_SSL(host_server)  # ssl登录

        # login(user,password):
        # user:登录邮箱的用户名。
        # password：登录邮箱的密码，像笔者用的是网易邮箱，网易邮箱一般是网页版，需要用到客户端密码，需要在网页版的网易邮箱中设置授权码，该授权码即为客户端密码。(NXJQDYEBREISFDWX)
        smtp.login(sender_qq, pwd)

        # sendmail(from_addr,to_addrs,msg,...):
        # from_addr:邮件发送者地址
        # to_addrs:邮件接收者地址。字符串列表['接收地址1','接收地址2','接收地址3',...]或'接收地址'
        # msg：发送消息：邮件内容。一般是msg.as_string():as_string()是将msg(MIMEText对象或者MIMEMultipart对象)变为str。
        smtp.sendmail(sender_qq, receiver, msg.as_string())

        # quit():用于结束SMTP会话。
        smtp.quit()
        logger.info("邮件发送成功，from = {}, to = {}, content = {}".format(sender_qq, receiver, mail_content))


    # 获取ip并对比
    def ip_render(self):
        try:
            new_ip = urlopen('http://icanhazip.com').read()
            current_ip = new_ip.decode(encoding='utf-8')
            logger.info('获取当前IP：{}'.format(current_ip))

            flag = self.compare_last_ip(current_ip)
            if flag:
                logger.info("发送邮件")
                self.send_email(current_ip)
        except Exception as e:
            logger.error("远程调用获取IP异常:{}".format(e))

        self.timer = threading.Timer(2 * 60 * 60, self.ip_render)  # 2小时 获取IP一次
        self.timer.start()


    # 对比上次获取的ip
    def compare_last_ip(self,current_ip):
        with open(file_name, "a+", encoding='utf-8') as input_file:
            last_ip = self.read_last_ip()
            logger.info('获取到最后一次记录的IP：{}'.format(last_ip))
            if len(last_ip) == 0:
                logger.info('获取到最后一次记录的IP：首次获取')
                input_file.write(current_ip)
                return True
            if last_ip != current_ip:
                logger.info('IP地址变化')
                input_file.write(current_ip)
                return True
        logger.info('IP地址无变化')
        return False


    # 读取上次保存的ip
    def read_last_ip(self):
        try:
            with open(file_name, "r", encoding='utf-8') as read_file:
                contents = read_file.readlines()
                if (len(contents) > 0):
                    return contents[-1]
                else:
                    return ''
        except FileNotFoundError:
            logger.error("ip.txt文件不存在")
            return ''



    def main(self):
        while self.is_running:
            logging.info('Service is running...')
            self.timer = threading.Timer(5, self.ip_render)  # 5s后开始循环线程
            self.timer.daemon = True  # 设为守护线程，随主线程退出
            self.timer.start()
	    # 使用事件等待而非循环
            win32event.WaitForSingleObject(self.hWaitStop, win32event.INFINITE)
            #print("1111111111111111111111111")
            # 在这里编写你的任务代码
            #time.sleep(5)#在这个示例中，我们定义了一个名为MyService的类，继承自win32serviceutil.ServiceFramework。我们需要在这个类中实现SvcDoRun方法来定义服务的主逻辑。在本例中，我们简单地输出一条日志信息，并通过time.sleep(5)来模拟一个长时间运行的任务。

if __name__ == '__main__':
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(MyService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(MyService)
