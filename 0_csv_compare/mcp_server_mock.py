#!/usr/bin/env python3
"""
MCP服务器模拟器 - 兼容Python 3.9
用于解决MCP连接问题的临时解决方案
"""

import json
import http.server
import socketserver
import threading
import time
import sys
from datetime import datetime

class MCPMockHandler(http.server.SimpleHTTPRequestHandler):
    """MCP模拟服务器处理器"""
    
    def do_GET(self):
        """处理GET请求"""
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "version": "mock-1.0.0",
                "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
            }
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
        elif self.path == '/mcp/test':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {
                "test": "success",
                "message": "MCP模拟服务器运行正常",
                "timestamp": datetime.now().isoformat()
            }
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
        else:
            super().do_GET()
    
    def do_POST(self):
        """处理POST请求"""
        if self.path == '/mcp/feedback':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            response = {
                "status": "received",
                "message": "反馈已接收",
                "timestamp": datetime.now().isoformat(),
                "data_length": content_length
            }
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        """自定义日志格式"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] ==liuq debug== MCP Mock Server: {format % args}")

class MCPMockServer:
    """MCP模拟服务器"""
    
    def __init__(self, port=8000):
        self.port = port
        self.server = None
        self.thread = None
        self.running = False
    
    def start(self):
        """启动服务器"""
        try:
            self.server = socketserver.TCPServer(("", self.port), MCPMockHandler)
            self.thread = threading.Thread(target=self.server.serve_forever)
            self.thread.daemon = True
            self.thread.start()
            self.running = True
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{timestamp}] ==liuq debug== MCP模拟服务器已启动，端口: {self.port}")
            print(f"[{timestamp}] ==liuq debug== 健康检查: http://localhost:{self.port}/health")
            print(f"[{timestamp}] ==liuq debug== 测试接口: http://localhost:{self.port}/mcp/test")
            
            return True
        except Exception as e:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{timestamp}] ==liuq debug== 启动MCP模拟服务器失败: {e}")
            return False
    
    def stop(self):
        """停止服务器"""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.running = False
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{timestamp}] ==liuq debug== MCP模拟服务器已停止")
    
    def is_running(self):
        """检查服务器是否运行"""
        return self.running

def test_server_connection(port=8000):
    """测试服务器连接"""
    import urllib.request
    import urllib.error
    
    try:
        url = f"http://localhost:{port}/health"
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{timestamp}] ==liuq debug== 服务器连接测试成功")
            print(f"[{timestamp}] ==liuq debug== 响应数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
            return True
    except Exception as e:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] ==liuq debug== 服务器连接测试失败: {e}")
        return False

def main():
    """主函数"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] ==liuq debug== 启动MCP模拟服务器...")
    
    # 创建并启动服务器
    server = MCPMockServer(port=8000)
    
    if server.start():
        # 等待服务器启动
        time.sleep(2)
        
        # 测试连接
        if test_server_connection():
            print(f"[{timestamp}] ==liuq debug== MCP模拟服务器运行正常")
            print(f"[{timestamp}] ==liuq debug== 按 Ctrl+C 停止服务器")
            
            try:
                # 保持服务器运行
                while server.is_running():
                    time.sleep(1)
            except KeyboardInterrupt:
                print(f"\n[{timestamp}] ==liuq debug== 收到停止信号")
        else:
            print(f"[{timestamp}] ==liuq debug== 服务器连接测试失败")
    else:
        print(f"[{timestamp}] ==liuq debug== 无法启动MCP模拟服务器")
    
    # 停止服务器
    server.stop()
    print(f"[{timestamp}] ==liuq debug== MCP模拟服务器已关闭")

if __name__ == "__main__":
    main()
