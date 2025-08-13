#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
拖拽功能系统级修复工具
解决Windows系统中拖拽功能被阻止的问题
"""
import sys
import os
import ctypes
import subprocess
from ctypes import wintypes

def is_admin():
    """检查是否以管理员权限运行"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    """以管理员权限重新运行"""
    if is_admin():
        return True
    else:
        print("==liuq debug== 需要管理员权限来修复系统拖拽问题")
        print("==liuq debug== 正在请求管理员权限...")
        try:
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join(sys.argv), None, 1
            )
            return False
        except:
            print("==liuq debug== 无法获取管理员权限")
            return False

def check_uac_settings():
    """检查UAC设置"""
    print("==liuq debug== 检查UAC设置...")
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                           r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System")
        try:
            uac_level = winreg.QueryValueEx(key, "ConsentPromptBehaviorAdmin")[0]
            print(f"==liuq debug== UAC级别: {uac_level}")
            if uac_level > 2:
                print("==liuq debug== ⚠️ UAC级别较高，可能阻止拖拽操作")
                return False
            else:
                print("==liuq debug== ✅ UAC级别正常")
                return True
        except FileNotFoundError:
            print("==liuq debug== UAC设置未找到")
            return True
        finally:
            winreg.CloseKey(key)
    except Exception as e:
        print(f"==liuq debug== 检查UAC设置失败: {e}")
        return True

def fix_drag_drop_policy():
    """修复拖拽相关的组策略设置"""
    print("==liuq debug== 修复拖拽组策略设置...")
    try:
        import winreg
        
        # 修复拖拽策略
        policies = [
            (winreg.HKEY_LOCAL_MACHINE, 
             r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer",
             "NoDrives", 0),
            (winreg.HKEY_CURRENT_USER,
             r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer", 
             "NoDrives", 0),
            (winreg.HKEY_LOCAL_MACHINE,
             r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer",
             "NoViewOnDrive", 0),
        ]
        
        for hkey, subkey, value_name, value_data in policies:
            try:
                key = winreg.CreateKey(hkey, subkey)
                winreg.SetValueEx(key, value_name, 0, winreg.REG_DWORD, value_data)
                winreg.CloseKey(key)
                print(f"==liuq debug== ✅ 修复策略: {value_name}")
            except Exception as e:
                print(f"==liuq debug== ⚠️ 修复策略失败 {value_name}: {e}")
        
        return True
    except Exception as e:
        print(f"==liuq debug== 修复组策略失败: {e}")
        return False

def enable_drag_drop_service():
    """启用拖拽相关的Windows服务"""
    print("==liuq debug== 检查并启用拖拽相关服务...")
    
    services = ["Themes", "UxSms", "DcomLaunch"]
    
    for service in services:
        try:
            result = subprocess.run(
                ["sc", "query", service], 
                capture_output=True, text=True, shell=True
            )
            if "RUNNING" in result.stdout:
                print(f"==liuq debug== ✅ 服务 {service} 正在运行")
            else:
                print(f"==liuq debug== ⚠️ 启动服务 {service}...")
                subprocess.run(["sc", "start", service], shell=True)
        except Exception as e:
            print(f"==liuq debug== 检查服务 {service} 失败: {e}")

def fix_file_associations():
    """修复文件关联问题"""
    print("==liuq debug== 修复文件关联...")
    try:
        # 重新注册拖拽相关的DLL
        dlls = ["ole32.dll", "shell32.dll", "user32.dll"]
        
        for dll in dlls:
            try:
                subprocess.run(["regsvr32", "/s", dll], shell=True)
                print(f"==liuq debug== ✅ 重新注册 {dll}")
            except Exception as e:
                print(f"==liuq debug== ⚠️ 注册 {dll} 失败: {e}")
        
        return True
    except Exception as e:
        print(f"==liuq debug== 修复文件关联失败: {e}")
        return False

def main():
    print("==liuq debug== 拖拽功能系统级修复工具启动")
    print("==liuq debug== 正在诊断和修复Windows拖拽功能问题...")
    
    # 检查管理员权限
    if not run_as_admin():
        print("==liuq debug== 需要管理员权限，程序退出")
        return
    
    print("==liuq debug== ✅ 已获得管理员权限")
    
    # 执行修复步骤
    steps = [
        ("检查UAC设置", check_uac_settings),
        ("修复拖拽组策略", fix_drag_drop_policy),
        ("启用相关服务", enable_drag_drop_service),
        ("修复文件关联", fix_file_associations),
    ]
    
    success_count = 0
    for step_name, step_func in steps:
        print(f"\n==liuq debug== 执行步骤: {step_name}")
        try:
            if step_func():
                success_count += 1
                print(f"==liuq debug== ✅ {step_name} 完成")
            else:
                print(f"==liuq debug== ⚠️ {step_name} 部分完成")
        except Exception as e:
            print(f"==liuq debug== ❌ {step_name} 失败: {e}")
    
    print(f"\n==liuq debug== 修复完成，成功执行 {success_count}/{len(steps)} 个步骤")
    print("==liuq debug== 建议重启计算机以确保所有更改生效")
    print("==liuq debug== 重启后请重新测试拖拽功能")

if __name__ == "__main__":
    main()
