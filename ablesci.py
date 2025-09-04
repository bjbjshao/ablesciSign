#!/usr/bin/env python
# cron:40 7 * * *
# new Env("科研通签到")
# coding=utf-8

# 标准库导入
import os
import re
import random
import time
import datetime
from typing import Dict, Any, Iterator

# 第三方库导入
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from cachetools import cached, TTLCache

# 本地模块导入
from sendNotify import send  # 消息通知模块


def generate_interval() -> float:
    """生成1-5秒随机请求间隔"""
    return random.uniform(1, 5)

# 缓存配置（1小时更新）
ua_cache = TTLCache(maxsize=100, ttl=3600)

@cached(ua_cache)
def generate_user_agent(platform: str) -> str:
    """
    生成随机用户代理字符串(User-Agent)
    """
    try:
        # 更合理的版本号范围
        current_year = datetime.datetime.now().year
        base_version = 120  # Chrome 120是2023年发布的合理版本
        major_version = random.randint(base_version, base_version + (current_year - 2023))
        
        platforms = {
            "desktop": {
                "chrome": f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{major_version}.0.0.0 Safari/537.36",
                "firefox": f"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:{major_version}.0) Gecko/20100101 Firefox/{major_version}.0",
                "edge": f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{major_version}.0.0.0 Safari/537.36 Edg/{major_version}.0.0.0"
            },
            "mobile": {
                "chrome": f"Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{major_version}.0.0.0 Mobile Safari/537.36",
                "firefox": f"Mozilla/5.0 (Android 13; Mobile; rv:{major_version}.0) Gecko/{major_version}.0 Firefox/{major_version}.0",
                "safari": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"
            }
        }
        
        browser_type = random.choice(list(platforms[platform].keys()))
        return platforms[platform][browser_type]
    except Exception as e:
        print(f"UA生成异常: {str(e)}")
        return 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'


def get_headers(cookie: str) -> Dict[str, str]:
    is_mobile = random.choice([True, False])
    user_agent = generate_user_agent('mobile' if is_mobile else 'desktop')

    headers = {
        'authority': 'www.ablesci.com',
        'accept': 'application/json, text/javascript, */*; q=0.01',
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'cookie': cookie,
        'referer': 'https://www.ablesci.com/',
        'user-agent': user_agent,
        'x-requested-with': 'XMLHttpRequest'
    }
    
    return headers


def create_session(retries: int = 3) -> requests.Session:
    """
    创建带重试机制的HTTP会话
    """
    session = requests.Session()
    retry = Retry(
        total=retries,
        backoff_factor=0.5,
        status_forcelist=[500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


def ablesci(cookie: str) -> Dict[str, Any]:
    url = "https://www.ablesci.com/user/sign"
    session = create_session()
    try:
        response = session.get(url, headers=get_headers(cookie), timeout=10)
        response.raise_for_status()
        print("成功访问签到接口")
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {str(e)}")
        return {'code': -1, 'msg': '网络请求失败'}


def ablesci_index(cookie: str) -> str:
    url = "https://www.ablesci.com/my/home"
    session = create_session()
    try:
        response = session.get(url, headers=get_headers(cookie), timeout=10)
        response.raise_for_status()
        html = response.text

        links = re.findall(r'<title.*?>(.+?)</title>', html)
        links2 = re.findall(r'<span style="color: #FF7200;.*?>(.+?)</span>', html)
        return f"{''.join(links)}{''.join(links2)}\n"
    except requests.exceptions.RequestException as e:
        print(f"主页请求失败: {str(e)}")
        return ""


def cookies() -> Iterator[str]:
    """
    从环境变量解析科研通多账号cookie配置
    """
    cookie_env = os.environ.get('ABLESCICOOKIE', '')
    if not cookie_env.strip():
        print("\033[31m[严重错误] 环境变量ABLESCICOOKIE未设置或为空！\033[0m")
        return
    cookies = cookie_env.splitlines()
    pattern = re.compile(r'^(cookie\d+=)?(.+?)$', re.MULTILINE)
    
    for entry in cookies:
        entry = entry.strip()
        if not entry:
            continue
        match = pattern.search(entry)
        if match:
            yield match.group(2).strip() if match.group(2) else match.group(1).strip()
        else:
            print(f"[警告] Cookie格式错误: {entry}")


if __name__ == "__main__":
    content = "="*26 + "\n"
    cookies_found = False
    for i, cookie in enumerate(cookies()):
        if not cookie:
            continue
        cookies_found = True

        interval = generate_interval()
        time.sleep(interval)

        result = ablesci(cookie)
        profile = ablesci_index(cookie)

        # 只添加登录状态信息
        content += f"账号{i+1}签到状态: "
        if result.get('code') == 0:
            content += "✅ 签到成功\n"
        else:
            content += f"❌ 签到失败 - {result.get('msg', '未知错误')}\n"

        time.sleep(interval)

    if not cookies_found:
        content += "\033[31m[错误] 未找到任何有效的cookie配置，请检查环境变量ABLESCICOOKIE是否正确设置\033[0m\n"
    
    content += "="*26
    print(content)
    send("科研通签到", content)
