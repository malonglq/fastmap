#!/usr/bin/env python3
"""
MCP最终连接测试
验证MCP服务器连接是否已修复
"""

import json
import urllib.request
import urllib.error
import sys
import os
from datetime import datetime

def log_debug(message):
    """调试日志输出"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] ==liuq debug== {message}")

def test_mcp_connection():
    """测试MCP连接"""
    log_debug("开始MCP连接最终测试...")
    
    tests = []
    
    # 测试1: 检查配置文件
    try:
        with open('mcp.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        log_debug("✅ MCP配置文件读取成功")
        tests.append(("配置文件", True, "配置文件存在且格式正确"))
    except Exception as e:
        log_debug(f"❌ MCP配置文件读取失败: {e}")
        tests.append(("配置文件", False, f"配置文件错误: {e}"))
        return tests
    
    # 测试2: 健康检查
    try:
        url = "http://localhost:8000/health"
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
        log_debug(f"✅ 健康检查通过: {data['status']}")
        tests.append(("健康检查", True, f"服务器状态: {data['status']}"))
    except Exception as e:
        log_debug(f"❌ 健康检查失败: {e}")
        tests.append(("健康检查", False, f"健康检查失败: {e}"))
    
    # 测试3: MCP测试接口
    try:
        url = "http://localhost:8000/mcp/test"
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
        log_debug(f"✅ MCP测试接口通过: {data['test']}")
        tests.append(("MCP接口", True, f"测试结果: {data['test']}"))
    except Exception as e:
        log_debug(f"❌ MCP测试接口失败: {e}")
        tests.append(("MCP接口", False, f"接口测试失败: {e}"))
    
    # 测试4: 反馈接口
    try:
        url = "http://localhost:8000/mcp/feedback"
        test_data = json.dumps({"test": "feedback", "timestamp": datetime.now().isoformat()})
        req = urllib.request.Request(url, data=test_data.encode('utf-8'), headers={'Content-Type': 'application/json'})
        
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
        log_debug(f"✅ 反馈接口通过: {data['status']}")
        tests.append(("反馈接口", True, f"反馈状态: {data['status']}"))
    except Exception as e:
        log_debug(f"❌ 反馈接口失败: {e}")
        tests.append(("反馈接口", False, f"反馈接口失败: {e}"))
    
    return tests

def generate_final_report(tests):
    """生成最终测试报告"""
    log_debug("生成MCP最终测试报告...")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"test_reports/mcp_final_test_{timestamp}.html"
    
    # 确保目录存在
    os.makedirs("test_reports", exist_ok=True)
    
    total_tests = len(tests)
    passed_tests = sum(1 for _, passed, _ in tests if passed)
    success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
    
    status_icon = "✅" if success_rate == 100 else "⚠️" if success_rate > 50 else "❌"
    status_text = "连接成功" if success_rate == 100 else "部分问题" if success_rate > 50 else "连接失败"
    status_class = "success" if success_rate == 100 else "warning" if success_rate > 50 else "error"
    
    test_items = ""
    for test_name, passed, details in tests:
        item_class = "passed" if passed else "failed"
        item_icon = "✅" if passed else "❌"
        item_status = "通过" if passed else "失败"
        
        test_items += f"""
            <div class="test-item {item_class}">
                <h4>{item_icon} {test_name}</h4>
                <p><strong>状态:</strong> {item_status}</p>
                <p><strong>详情:</strong> {details}</p>
            </div>"""
    
    html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MCP 最终测试报告</title>
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
        .conclusion {{ background: #e7f3ff; padding: 20px; border-radius: 6px; margin: 20px 0; }}
        .conclusion.success {{ background: #d4edda; border: 1px solid #c3e6cb; }}
        .conclusion.warning {{ background: #fff3cd; border: 1px solid #ffeaa7; }}
        .conclusion.error {{ background: #f8d7da; border: 1px solid #f5c6cb; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔧 MCP 最终测试报告</h1>
            <div class="status {status_class}">
                {status_icon} {status_text}
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
            {test_items}
        </div>
        
        <div class="conclusion {status_class}">
            <h2>📝 测试结论</h2>
            <p><strong>总体状态:</strong> {status_text}</p>
            <p><strong>成功率:</strong> {success_rate:.1f}%</p>
            {'<p><strong>结论:</strong> 🎉 MCP服务器连接问题已解决！所有测试通过，系统运行正常。</p>' if success_rate == 100 else 
             '<p><strong>结论:</strong> ⚠️ MCP服务器部分功能正常，建议检查失败的测试项目。</p>' if success_rate > 50 else 
             '<p><strong>结论:</strong> ❌ MCP服务器连接仍有问题，需要进一步排查。</p>'}
        </div>
        
        <div class="footer" style="text-align: center; margin-top: 30px; color: #666; font-size: 12px;">
            <p>MCP 最终测试工具 | 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>
</body>
</html>
"""
    
    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        log_debug(f"最终测试报告已生成: {report_file}")
        return report_file
    except Exception as e:
        log_debug(f"生成最终测试报告失败: {e}")
        return None

def main():
    """主函数"""
    log_debug("开始MCP最终连接测试...")
    
    # 运行测试
    tests = test_mcp_connection()
    
    # 生成报告
    report_file = generate_final_report(tests)
    
    # 输出结果
    total_tests = len(tests)
    passed_tests = sum(1 for _, passed, _ in tests if passed)
    success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
    
    log_debug(f"测试完成: {passed_tests}/{total_tests} 通过 ({success_rate:.1f}%)")
    
    if success_rate == 100:
        log_debug("🎉 恭喜！MCP服务器连接问题已完全解决！")
    elif success_rate > 50:
        log_debug("⚠️ MCP服务器部分功能正常，建议检查失败项目")
    else:
        log_debug("❌ MCP服务器连接仍有问题，需要进一步排查")
    
    if report_file:
        log_debug(f"详细报告: {report_file}")

if __name__ == "__main__":
    main()
