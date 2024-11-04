import json
import os
import re
import sys

import requests
import wx

from Log import Log

log = Log()  # 假设Log类是单例或者你已经创建了一个Log类的实例


class LoginFrame(wx.Frame):
    def __init__(self, parent, title):
        super(LoginFrame, self).__init__(parent, title=title, size=(400, 400))
        self.InitUI()

    def InitUI(self):
        # 设置窗口图标
        if getattr(sys, 'frozen', False):
            # 如果程序被打包，则从临时目录加载资源
            application_path = sys._MEIPASS
        else:
            # 如果程序没有被打包，则从当前工作目录加载资源
            application_path = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(application_path, 'SchoolWIFI.ico')
        if os.path.exists(icon_path):
            icon = wx.Icon(icon_path, wx.BITMAP_TYPE_ICO)
            self.SetIcon(icon)

        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        # 添加手机号（账号）和密码输入框
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        self.phoneText = wx.TextCtrl(panel, style=wx.TE_LEFT)
        hbox1.Add(wx.StaticText(panel, label="手机:"), flag=wx.RIGHT, border=8)
        hbox1.Add(self.phoneText, proportion=1, flag=wx.EXPAND | wx.LEFT, border=8)
        vbox.Add(hbox1, flag=wx.EXPAND | wx.ALL, border=5)

        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        self.passwordText = wx.TextCtrl(panel, style=wx.TE_LEFT | wx.TE_PASSWORD)
        hbox2.Add(wx.StaticText(panel, label="密码:"), flag=wx.RIGHT, border=8)
        hbox2.Add(self.passwordText, proportion=1, flag=wx.EXPAND | wx.LEFT, border=8)
        vbox.Add(hbox2, flag=wx.EXPAND | wx.ALL, border=5)

        # 创建一个新的水平盒子来放置登录和注销按钮
        buttonBoxTop = wx.BoxSizer(wx.HORIZONTAL)
        loginButton = wx.Button(panel, label='登陆')
        loginButton.Bind(wx.EVT_BUTTON, self.OnLogin)
        logoutButton = wx.Button(panel, label='注销')
        logoutButton.Bind(wx.EVT_BUTTON, self.OnLogout)
        buttonBoxTop.Add(loginButton, proportion=1, flag=wx.EXPAND | wx.ALL, border=5)
        buttonBoxTop.Add(logoutButton, proportion=1, flag=wx.EXPAND | wx.ALL, border=5)
        vbox.Add(buttonBoxTop, flag=wx.EXPAND | wx.ALL, border=10)

        # 登录列表框
        self.listBox = wx.ListBox(panel, style=wx.LB_SINGLE)
        vbox.Add(self.listBox, proportion=1, flag=wx.EXPAND | wx.ALL, border=10)

        # 创建另一个水平盒子来放置添加和删除账号按钮
        buttonBoxBottom = wx.BoxSizer(wx.HORIZONTAL)
        addAccountButton = wx.Button(panel, label='添加')
        addAccountButton.Bind(wx.EVT_BUTTON, self.OnAddAccount)
        deleteAccountButton = wx.Button(panel, label='删除')
        deleteAccountButton.Bind(wx.EVT_BUTTON, self.OnDeleteAccount)
        buttonBoxBottom.Add(addAccountButton, proportion=1, flag=wx.EXPAND | wx.ALL, border=5)
        buttonBoxBottom.Add(deleteAccountButton, proportion=1, flag=wx.EXPAND | wx.ALL, border=5)
        vbox.Add(buttonBoxBottom, flag=wx.EXPAND | wx.ALL, border=10)

        panel.SetSizer(vbox)
        vbox.Layout()  # 布局垂直盒子
        panel.Fit()  # 调整面板大小以适应内容
        self.Centre()  # 居中窗口
        self.SetTitle("校园网登陆GUI")
        self.LoadCredentials()

    def LoadCredentials(self):
        credentials = self.GetCredentials()  # 从加密存储中加载凭证
        self.listBox.Clear()  # 清空列表框
        for credential in credentials:
            masked_credential = self.mask_phone_number(credential)
            self.listBox.Append(masked_credential)
        if credentials:  # 如果有凭证，选择第一个
            self.listBox.SetSelection(0)

    def GetCredentials(self):
        return log.get_credentials()

    def mask_phone_number(self, phone_number):
        # 将手机号中间的数字替换为星号(*)，保留前三位和后两位
        if len(phone_number) == 11 and phone_number.startswith('1'):
            return phone_number[:3] + "****" + phone_number[-2:]
        return phone_number

    def OnAddAccount(self, event):
        phone = self.phoneText.GetValue()
        password = self.passwordText.GetValue()

        # 手机号格式验证
        if not re.match(r'^1\d{10}$', phone):
            wx.MessageBox("手机号格式不正确", "错误", wx.OK | wx.ICON_ERROR)
            return

        if phone and password:  # 确保手机号和密码不为空
            masked_phone = self.mask_phone_number(phone)
            if masked_phone not in self.GetCredentials():  # 检查手机号（账号）是否已存在
                log.save_credentials(phone, password)  # 保存凭证
                self.LoadCredentials()  # 重新加载凭证列表
                self.phoneText.Clear()  # 清空输入框
                self.passwordText.Clear()
            else:
                wx.MessageBox("账号已存在！", "错误", wx.OK | wx.ICON_ERROR)
        else:
            wx.MessageBox("手机号和密码不能为空！", "错误", wx.OK | wx.ICON_ERROR)

    def OnLogin(self, event):
        selection_index = self.listBox.GetSelection()
        if selection_index == wx.NOT_FOUND:
            wx.MessageBox("没有选择任何用户数据，请先添加账号。", "错误", wx.OK | wx.ICON_ERROR)
            return
        if selection_index != wx.NOT_FOUND:
            selection = self.listBox.GetString(selection_index)
            original_phone = self.get_original_phone(selection)
            decrypted_password = log.get_decrypted_password(original_phone)
            self.perform_login(original_phone, decrypted_password)

    def get_original_phone(self, masked_phone):
        # 根据掩码手机号获取原始手机号
        credentials = self.GetCredentials()
        for phone, (masked, _) in credentials.items():
            if self.mask_phone_number(phone) == masked_phone:
                return phone
        return None

    def OnLogout(self, event):
        self.perform_logout()

    def perform_login(self, username, password):
        url = "http://59.52.20.94:801/eportal/portal/login"
        params = {
            'callback': 'liejiu',
            'user_account': username + "@telecom",
            'user_password': password
        }
        try:
            response = requests.get(url, params=params, timeout=3)
            response.raise_for_status()  # 如果响应状态码不是 200，将抛出异常

            # 从响应内容中提取 JSON 数据
            json_str = response.text[7:-2]  # 去掉 'liejiu(' 和 ')'
            data = json.loads(json_str)  # 将 JSON 字符串转换为 Python 字典

            # 根据返回的状态码进行处理
            if data.get("result") == 1:
                wx.MessageBox("登录成功", "成功", wx.OK | wx.ICON_INFORMATION)
            else:
                wx.MessageBox(data.get("msg"), "错误", wx.OK | wx.ICON_ERROR)
        except requests.RequestException as e:
            wx.MessageBox("请求失败: 请检查网络连接", "错误", wx.OK | wx.ICON_ERROR)

    def perform_logout(self):
        url = "http://59.52.20.94:801/eportal/portal/logout"
        params = {
            'callback': 'liejiu'
        }
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()  # 如果响应状态码不是 200，将抛出异常

            # 从响应内容中提取 JSON 数据
            json_str = response.text[7:-2]  # 去掉 'liejiu(' 和 ')'
            data = json.loads(json_str)  # 将 JSON 字符串转换为 Python 字典

            # 根据返回的状态码进行处理
            if data.get('result') == 1:
                wx.MessageBox("注销成功", "成功", wx.OK | wx.ICON_INFORMATION)
            else:
                wx.MessageBox(data.get("msg"), "错误", wx.OK | wx.ICON_ERROR)
        except requests.RequestException as e:
            wx.MessageBox("请求失败: 请检查网络连接或URL是否正确。", "错误", wx.OK | wx.ICON_ERROR)

    def OnDeleteAccount(self, event):
        selection_index = self.listBox.GetSelection()
        if selection_index == wx.NOT_FOUND:
            wx.MessageBox("没有选择任何账号，请先选择一个账号。", "错误", wx.OK | wx.ICON_ERROR)
            return

        selection = self.listBox.GetString(selection_index)
        original_phone = self.get_original_phone(selection)
        if log.remove_credentials(original_phone):  # 使用Log类的remove_credentials方法
            self.LoadCredentials()  # 重新加载凭证列表
            wx.MessageBox("账号删除成功。", "成功", wx.OK | wx.ICON_INFORMATION)
        else:
            wx.MessageBox("账号删除失败，请重试。", "错误", wx.OK | wx.ICON_ERROR)


class MyApp(wx.App):
    def OnInit(self):
        frame = LoginFrame(None, "Login App")
        frame.Show()
        return True


if __name__ == "__main__":
    app = wx.App()
    frame = LoginFrame(None, "Login App")
    frame.Show()
    app.MainLoop()
