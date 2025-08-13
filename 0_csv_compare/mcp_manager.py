#!/usr/bin/env python3
"""
MCP管理器 - 一键管理MCP服务器
提供启动、停止、状态检查、测试等功能
"""

import json
import subprocess
import sys
import time
import urllib.request
import urllib.error
import os
from datetime import datetime

class MCPManager:
    """MCP服务器管理器"""
    
    def __init__(self):
        self.server_process = None
        self.server_url = "http://localhost:8000"
        self.config_file = "mcp.json"
        self.server_script = "mcp_server_mock.py"
    
    def log_debug(self, message):
        """调试日志输出"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] ==liuq debug== {message}")
    
    def check_server_status(self):
        """检查服务器状态"""
        try:
            url = f"{self.server_url}/health"
            with urllib.request.urlopen(url, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
                return True, data
        except Exception as e:
            return False, str(e)
    
    def start_server(self):
        """启动MCP服务器"""
        self.log_debug("启动MCP服务器...")
        
        # 检查服务器是否已经运行
        is_running, status = self.check_server_status()
        if is_running:
            self.log_debug("MCP服务器已经在运行中")
            return True
        
        # 检查服务器脚本是否存在
        if not os.path.exists(self.server_script):
            self.log_debug(f"错误: 服务器脚本 {self.server_script} 不存在")
            return False
        
        try:
            # 启动服务器进程
            self.server_process = subprocess.Popen([
                "python", self.server_script
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # 等待服务器启动
            self.log_debug("等待服务器启动...")
            for i in range(10):  # 最多等待10秒
                time.sleep(1)
                is_running, status = self.check_server_status()
                if is_running:
                    self.log_debug("✅ MCP服务器启动成功")
                    return True
                self.log_debug(f"等待中... ({i+1}/10)")
            
            self.log_debug("❌ MCP服务器启动超时")
            return False
            
        except Exception as e:
            self.log_debug(f"❌ 启动MCP服务器失败: {e}")
            return False
    
    def stop_server(self):
        """停止MCP服务器"""
        self.log_debug("停止MCP服务器...")
        
        if self.server_process:
            try:
                self.server_process.terminate()
                self.server_process.wait(timeout=5)
                self.log_debug("✅ MCP服务器已停止")
                return True
            except Exception as e:
                self.log_debug(f"❌ 停止MCP服务器失败: {e}")
                return False
        else:
            self.log_debug("没有找到运行中的服务器进程")
            return True
    
    def test_connection(self):
        """测试MCP连接"""
        self.log_debug("测试MCP连接...")
        
        tests = []
        
        # 健康检查
        is_running, status = self.check_server_status()
        if is_running:
            self.log_debug("✅ 健康检查通过")
            tests.append(("健康检查", True))
        else:
            self.log_debug(f"❌ 健康检查失败: {status}")
            tests.append(("健康检查", False))
        
        # MCP测试接口
        try:
            url = f"{self.server_url}/mcp/test"
            with urllib.request.urlopen(url, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
            self.log_debug("✅ MCP测试接口通过")
            tests.append(("MCP接口", True))
        except Exception as e:
            self.log_debug(f"❌ MCP测试接口失败: {e}")
            tests.append(("MCP接口", False))
        
        # 反馈接口
        try:
            url = f"{self.server_url}/mcp/feedback"
            test_data = json.dumps({"test": "connection", "timestamp": datetime.now().isoformat()})
            req = urllib.request.Request(url, data=test_data.encode('utf-8'), headers={'Content-Type': 'application/json'})
            
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
            self.log_debug("✅ 反馈接口通过")
            tests.append(("反馈接口", True))
        except Exception as e:
            self.log_debug(f"❌ 反馈接口失败: {e}")
            tests.append(("反馈接口", False))
        
        # 输出测试结果
        passed = sum(1 for _, result in tests if result)
        total = len(tests)
        success_rate = (passed / total) * 100 if total > 0 else 0
        
        self.log_debug(f"测试完成: {passed}/{total} 通过 ({success_rate:.1f}%)")
        
        return success_rate == 100
    
    def show_status(self):
        """显示服务器状态"""
        self.log_debug("检查MCP服务器状态...")
        
        is_running, status = self.check_server_status()
        
        if is_running:
            self.log_debug("🟢 MCP服务器运行正常")
            self.log_debug(f"   服务器地址: {self.server_url}")
            self.log_debug(f"   服务器状态: {status.get('status', 'unknown')}")
            self.log_debug(f"   服务器版本: {status.get('version', 'unknown')}")
            self.log_debug(f"   Python版本: {status.get('python_version', 'unknown')}")
        else:
            self.log_debug("🔴 MCP服务器未运行")
            self.log_debug(f"   错误信息: {status}")
        
        return is_running
    
    def show_help(self):
        """显示帮助信息"""
        help_text = """
MCP管理器 - 使用说明

命令:
  start    - 启动MCP服务器
  stop     - 停止MCP服务器
  status   - 查看服务器状态
  test     - 测试服务器连接
  restart  - 重启服务器
  help     - 显示此帮助信息

示例:
  python mcp_manager.py start
  python mcp_manager.py status
  python mcp_manager.py test
  python mcp_manager.py stop

服务器地址: http://localhost:8000
配置文件: mcp.json
"""
        print(help_text)

def main():
    """主函数"""
    manager = MCPManager()
    
    if len(sys.argv) < 2:
        manager.show_help()
        return
    
    command = sys.argv[1].lower()
    
    if command == "start":
        success = manager.start_server()
        if success:
            manager.log_debug("🎉 MCP服务器启动完成")
        else:
            manager.log_debug("❌ MCP服务器启动失败")
            sys.exit(1)
    
    elif command == "stop":
        success = manager.stop_server()
        if success:
            manager.log_debug("✅ MCP服务器停止完成")
        else:
            manager.log_debug("❌ MCP服务器停止失败")
            sys.exit(1)
    
    elif command == "status":
        manager.show_status()
    
    elif command == "test":
        success = manager.test_connection()
        if success:
            manager.log_debug("🎉 所有测试通过，MCP连接正常")
        else:
            manager.log_debug("⚠️ 部分测试失败，请检查服务器状态")
    
    elif command == "restart":
        manager.log_debug("重启MCP服务器...")
        manager.stop_server()
        time.sleep(2)
        success = manager.start_server()
        if success:
            manager.log_debug("🎉 MCP服务器重启完成")
        else:
            manager.log_debug("❌ MCP服务器重启失败")
            sys.exit(1)
    
    elif command == "help":
        manager.show_help()
    
    else:
        manager.log_debug(f"未知命令: {command}")
        manager.show_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
