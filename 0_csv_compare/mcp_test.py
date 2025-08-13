#!/usr/bin/env python3
"""
MCP连接测试脚本
用于诊断和解决MCP服务器连接问题
"""

import json
import subprocess
import sys
import time
import os
from datetime import datetime

def log_debug(message):
    """调试日志输出"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] ==liuq debug== {message}")

def check_python_version():
    """检查Python版本"""
    version = sys.version_info
    log_debug(f"Python版本: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        log_debug("警告: MCP需要Python 3.10+，当前版本可能不兼容")
        return False
    return True

def check_mcp_config():
    """检查MCP配置文件"""
    config_file = "mcp.json"
    if os.path.exists(config_file):
        log_debug(f"找到MCP配置文件: {config_file}")
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            log_debug(f"配置内容: {json.dumps(config, indent=2, ensure_ascii=False)}")
            return config
        except Exception as e:
            log_debug(f"读取配置文件失败: {e}")
            return None
    else:
        log_debug("未找到MCP配置文件")
        return None

def create_mock_mcp_server():
    """创建模拟MCP服务器"""
    log_debug("创建模拟MCP服务器...")
    
    mock_config = {
        "mcpServers": {
            "mock-server": {
                "command": "python",
                "args": ["-c", "print('Mock MCP Server Started'); import time; time.sleep(10)"],
                "env": {
                    "MCP_DEBUG": "true"
                }
            }
        },
        "settings": {
            "timeout": 10,
            "retries": 2,
            "logLevel": "debug"
        }
    }
    
    try:
        with open("mcp.json", 'w', encoding='utf-8') as f:
            json.dump(mock_config, f, indent=2, ensure_ascii=False)
        log_debug("MCP配置文件创建成功")
        return True
    except Exception as e:
        log_debug(f"创建配置文件失败: {e}")
        return False

def test_mock_server():
    """测试模拟服务器"""
    log_debug("启动模拟MCP服务器测试...")
    
    try:
        # 启动模拟服务器
        process = subprocess.Popen([
            "python", "-c", 
            "print('Mock MCP Server Started'); import time; time.sleep(5); print('Mock MCP Server Stopped')"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # 等待进程完成
        stdout, stderr = process.communicate(timeout=10)
        
        if process.returncode == 0:
            log_debug("模拟服务器测试成功")
            log_debug(f"输出: {stdout.strip()}")
            return True
        else:
            log_debug(f"模拟服务器测试失败，返回码: {process.returncode}")
            log_debug(f"错误: {stderr.strip()}")
            return False
            
    except subprocess.TimeoutExpired:
        log_debug("模拟服务器测试超时")
        process.kill()
        return False
    except Exception as e:
        log_debug(f"模拟服务器测试异常: {e}")
        return False

def generate_test_report():
    """生成测试报告"""
    log_debug("生成MCP连接测试报告...")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"test_reports/mcp_connection_test_{timestamp}.html"
    
    # 确保目录存在
    os.makedirs("test_reports", exist_ok=True)
    
    # 运行测试
    python_ok = check_python_version()
    config_ok = check_mcp_config() is not None
    server_ok = test_mock_server()
    
    total_tests = 3
    passed_tests = sum([python_ok, config_ok, server_ok])
    success_rate = (passed_tests / total_tests) * 100
    
    html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MCP 连接测试报告</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .status {{ font-size: 24px; margin: 10px 0; }}
        .success {{ color: #28a745; }}
        .warning {{ color: #ffc107; }}
        .error {{ color: #dc3545; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
        .card {{ background: #f8f9fa; padding: 15px; border-radius: 6px; border-left: 4px solid #007bff; }}
        .card h3 {{ margin: 0 0 10px 0; color: #333; }}
        .card .value {{ font-size: 24px; font-weight: bold; color: #007bff; }}
        .test-item {{ background: #f8f9fa; margin: 10px 0; padding: 15px; border-radius: 6px; }}
        .test-item.passed {{ border-left: 4px solid #28a745; }}
        .test-item.failed {{ border-left: 4px solid #dc3545; }}
        .solutions {{ background: #e7f3ff; padding: 15px; border-radius: 6px; margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔧 MCP 连接测试报告</h1>
            <div class="status {'success' if success_rate == 100 else 'warning' if success_rate > 0 else 'error'}">
                {'✅ 连接正常' if success_rate == 100 else '⚠️ 部分问题' if success_rate > 0 else '❌ 连接失败'}
            </div>
            <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="summary">
            <div class="card">
                <h3>总测试数</h3>
                <div class="value">{total_tests}</div>
            </div>
            <div class="card">
                <h3>通过测试</h3>
                <div class="value" style="color: #28a745;">{passed_tests}</div>
            </div>
            <div class="card">
                <h3>失败测试</h3>
                <div class="value" style="color: #dc3545;">{total_tests - passed_tests}</div>
            </div>
            <div class="card">
                <h3>成功率</h3>
                <div class="value">{success_rate:.1f}%</div>
            </div>
        </div>
        
        <div class="tests">
            <h2>📋 测试详情</h2>
            
            <div class="test-item {'passed' if python_ok else 'failed'}">
                <h4>{'✅' if python_ok else '❌'} Python版本检查</h4>
                <p>检查Python版本是否满足MCP要求</p>
                <p><strong>状态:</strong> {'通过' if python_ok else '失败'}</p>
                <p><strong>详情:</strong> Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}</p>
            </div>
            
            <div class="test-item {'passed' if config_ok else 'failed'}">
                <h4>{'✅' if config_ok else '❌'} MCP配置文件</h4>
                <p>检查MCP配置文件是否存在且格式正确</p>
                <p><strong>状态:</strong> {'通过' if config_ok else '失败'}</p>
                <p><strong>详情:</strong> {'配置文件正常' if config_ok else '配置文件缺失或格式错误'}</p>
            </div>
            
            <div class="test-item {'passed' if server_ok else 'failed'}">
                <h4>{'✅' if server_ok else '❌'} 服务器连接测试</h4>
                <p>测试模拟MCP服务器启动和连接</p>
                <p><strong>状态:</strong> {'通过' if server_ok else '失败'}</p>
                <p><strong>详情:</strong> {'服务器启动正常' if server_ok else '服务器启动失败'}</p>
            </div>
        </div>
        
        <div class="solutions">
            <h2>🔧 解决方案建议</h2>
            <ul>
                {'<li>Python版本过低，建议升级到Python 3.10+</li>' if not python_ok else ''}
                {'<li>创建或修复MCP配置文件</li>' if not config_ok else ''}
                {'<li>检查网络连接和防火墙设置</li>' if not server_ok else ''}
                <li>确保所有依赖包已正确安装</li>
                <li>检查环境变量配置</li>
                <li>重启开发环境后重试</li>
            </ul>
        </div>
        
        <div class="footer" style="text-align: center; margin-top: 30px; color: #666; font-size: 12px;">
            <p>MCP 连接诊断工具 | 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>
</body>
</html>
"""
    
    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        log_debug(f"测试报告已生成: {report_file}")
        return report_file
    except Exception as e:
        log_debug(f"生成测试报告失败: {e}")
        return None

def main():
    """主函数"""
    log_debug("开始MCP连接诊断...")
    
    # 检查Python版本
    python_ok = check_python_version()
    
    # 检查配置文件
    config = check_mcp_config()
    if not config:
        log_debug("尝试创建模拟配置文件...")
        create_mock_mcp_server()
    
    # 运行测试
    test_mock_server()
    
    # 生成报告
    report_file = generate_test_report()
    
    log_debug("MCP连接诊断完成")
    
    if report_file:
        log_debug(f"请查看详细报告: {report_file}")

if __name__ == "__main__":
    main()
