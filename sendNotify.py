#!/usr/bin/env python3
# _*_ coding:utf-8 _*_

"""
消息推送工具 - 支持息知、Server酱、PushPlus三种推送方式
提供统一的消息推送接口，支持多种通知渠道
"""

import sys
import os
import requests
import json
import time
from typing import Optional, List, Dict, Any

# 通知服务配置（可从环境变量读取）
SCKEY = os.environ.get("SCKEY", "")          # Server酱的SCKEY
XZKEY = os.environ.get("XZKEY", "")          # 息知的XZKEY
PUSH_PLUS_TOKEN = os.environ.get("PUSH_PLUS_TOKEN", "")  # PushPlus的Token

# 全局消息缓冲区
message_buffer = []

def add_message(msg: str) -> None:
    """
    添加消息到缓冲区
    
    Args:
        msg: 要添加的消息内容
    """
    print(f"📝 添加消息: {msg}")
    message_buffer.append(msg)

def get_message_content() -> str:
    """获取所有缓冲消息的内容"""
    return "\n".join(message_buffer)

def clear_messages() -> None:
    """清空消息缓冲区"""
    message_buffer.clear()
    print("🗑️  消息缓冲区已清空")

def server_jiang_push(title: str, content: str) -> bool:
    """
    Server酱推送实现
    
    Args:
        title: 消息标题
        content: 消息内容
        
    Returns:
        bool: 推送是否成功
    """
    print("🚀 开始Server酱推送")
    
    if not SCKEY:
        print("❌ Server酱SCKEY未配置，推送取消")
        return False
    
    try:
        # 构造请求数据
        payload = {
            "text": title,
            "desp": content.replace("\n", "\n\n")
        }
        
        # 发送请求
        start_time = time.time()
        response = requests.post(
            f"https://sctapi.ftqq.com/{SCKEY}.send",
            data=payload,
            timeout=15
        )
        response_time = time.time() - start_time
        
        # 解析响应
        response_data = response.json()
        print(f"📨 Server酱响应耗时: {response_time:.2f}s")
        
        if response_data.get('errno') == 0 or response_data.get('data', {}).get('errno') == 0:
            print("✅ Server酱推送成功")
            return True
        else:
            print(f"❌ Server酱推送失败: {response_data}")
            return False
            
    except requests.exceptions.Timeout:
        print("⏰ Server酱推送超时")
        return False
    except requests.exceptions.RequestException as e:
        print(f"🌐 Server酱网络请求失败: {str(e)}")
        return False
    except json.JSONDecodeError as e:
        print(f"📄 Server酱响应解析失败: {str(e)}")
        return False
    except Exception as e:
        print(f"⚠️  Server酱推送异常: {str(e)}")
        return False

def xizhi_push(title: str, content: str) -> bool:
    """
    息知推送实现
    
    Args:
        title: 消息标题
        content: 消息内容
        
    Returns:
        bool: 推送是否成功
    """
    print("🚀 开始息知推送")
    
    if not XZKEY:
        print("❌ 息知XZKEY未配置，推送取消")
        return False
    
    try:
        # 构造请求数据
        payload = {
            'title': title,
            'content': content.replace("\n", "\n\n")
        }
        
        # 设置请求头
        headers = {'Content-Type': 'application/json'}
        
        # 发送请求
        start_time = time.time()
        response = requests.post(
            f"https://xizhi.qqoq.net/{XZKEY}.send",
            data=json.dumps(payload),
            headers=headers,
            timeout=15
        )
        response_time = time.time() - start_time
        
        print(f"📨 息知响应状态码: {response.status_code}, 耗时: {response_time:.2f}s")
        
        if response.status_code == 200:
            print("✅ 息知推送成功")
            return True
        else:
            print(f"❌ 息知推送失败，状态码: {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print("⏰ 息知推送超时")
        return False
    except requests.exceptions.RequestException as e:
        print(f"🌐 息知网络请求失败: {str(e)}")
        return False
    except Exception as e:
        print(f"⚠️  息知推送异常: {str(e)}")
        return False

def pushplus_push(title: str, content: str) -> bool:
    """
    PushPlus推送实现
    
    Args:
        title: 消息标题
        content: 消息内容
        
    Returns:
        bool: 推送是否成功
    """
    print("🚀 开始PushPlus推送")
    
    if not PUSH_PLUS_TOKEN:
        print("❌ PushPlus Token未配置，推送取消")
        return False
    
    try:
        # 构造请求数据
        payload = {
            "token": PUSH_PLUS_TOKEN,
            "title": title,
            "content": content
        }
        
        # 设置请求头
        headers = {'Content-Type': 'application/json'}
        
        # 发送请求
        start_time = time.time()
        response = requests.post(
            'http://www.pushplus.plus/send',
            data=json.dumps(payload),
            headers=headers,
            timeout=15
        )
        response_time = time.time() - start_time
        
        # 解析响应
        response_data = response.json()
        print(f"📨 PushPlus响应耗时: {response_time:.2f}s")
        
        if response_data.get('code') == 200:
            print("✅ PushPlus推送成功")
            return True
        else:
            print(f"❌ PushPlus推送失败: {response_data.get('msg', '未知错误')}")
            return False
            
    except requests.exceptions.Timeout:
        print("⏰ PushPlus推送超时")
        return False
    except requests.exceptions.RequestException as e:
        print(f"🌐 PushPlus网络请求失败: {str(e)}")
        return False
    except json.JSONDecodeError as e:
        print(f"📄 PushPlus响应解析失败: {str(e)}")
        return False
    except Exception as e:
        print(f"⚠️  PushPlus推送异常: {str(e)}")
        return False

def send(title: str, content: str, use_buffer: bool = False) -> Dict[str, bool]:
    """
    发送消息到所有启用的推送渠道
    
    Args:
        title: 消息标题
        content: 消息内容
        use_buffer: 是否使用缓冲区内容
        
    Returns:
        Dict: 各推送渠道的结果字典
    """
    # 检查可用的推送服务
    notify_modes = []
    if SCKEY:
        notify_modes.append('sc_key')
    if XZKEY:
        notify_modes.append('xz_key')
    if PUSH_PLUS_TOKEN:
        notify_modes.append('pushplus_bot')
    
    if not notify_modes:
        print("⚠️  没有可用的推送服务，消息未发送")
        return {}
    
    print(f"📋 可用推送服务: {', '.join(notify_modes)}")
    
    # 确定要发送的内容
    final_content = get_message_content() if use_buffer and message_buffer else content
    
    if not final_content.strip():
        print("⚠️  消息内容为空，取消发送")
        return {}
    
    print(f"📤 开始发送消息: {title}")
    print(f"📄 消息内容长度: {len(final_content)} 字符")
    
    results = {}
    success_count = 0
    
    # 遍历所有启用的推送方式
    for mode in notify_modes:
        try:
            if mode == 'sc_key':
                result = server_jiang_push(title, final_content)
                results['server_jiang'] = result
                if result:
                    success_count += 1
            elif mode == 'xz_key':
                result = xizhi_push(title, final_content)
                results['xizhi'] = result
                if result:
                    success_count += 1
            elif mode == 'pushplus_bot':
                result = pushplus_push(title, final_content)
                results['pushplus'] = result
                if result:
                    success_count += 1
        except Exception as e:
            print(f"💥 推送模式 {mode} 执行异常: {str(e)}")
            results[mode] = False
    
    # 输出推送结果
    print(f"📊 推送完成，成功: {success_count}/{len(results)}")
    
    return results

def main():
    """测试函数"""
    print("=" * 50)
    print("🧪 开始测试推送服务")
    print("=" * 50)
    
    # 添加测试消息到缓冲区
    add_message("这是一条测试消息")
    add_message("第二行测试内容")
    add_message("最后一行内容")
    
    # 发送测试消息
    results = send(
        title="测试通知标题",
        content="这是直接传入的内容\n将会被缓冲区内容覆盖",
        use_buffer=True
    )
    
    print(f"📋 测试完成，结果: {results}")
    
    # 清空缓冲区
    clear_messages()

if __name__ == '__main__':
    main()
