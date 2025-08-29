#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试用例批量运行器
==liuq debug== FastMapV2 测试用例批量执行脚本

{{CHENGQI:
Action: Added; Timestamp: 2025-08-28 15:00:00 +08:00; Reason: 创建测试用例批量运行器; Principle_Applied: 测试自动化;
}}

作者: 龙sir团队
创建时间: 2025-08-28
版本: 2.0.0
描述: 批量运行所有测试用例脚本
"""

import sys
import subprocess
import logging
from pathlib import Path
from typing import List, Dict, Tuple

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('tests/test_results.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

class TestCaseRunner:
    """测试用例运行器"""
    
    def __init__(self):
        self.test_dir = Path(__file__).parent
        self.results: Dict[str, Dict] = {}
    
    def get_test_case_files(self) -> List[Path]:
        """获取所有测试用例文件"""
        test_files = []
        
        # 查找所有TC-开头的测试文件
        for test_file in self.test_dir.rglob("TC-*.py"):
            test_files.append(test_file)
        
        # 按文件名排序
        test_files.sort(key=lambda x: x.name)
        
        logger.info(f"==liuq debug== 找到{len(test_files)}个测试用例文件")
        return test_files
    
    def run_single_test(self, test_file: Path) -> Tuple[bool, str, str]:
        """运行单个测试文件"""
        logger.info(f"==liuq debug== 运行测试: {test_file.name}")
        
        try:
            # 使用pytest运行测试
            result = subprocess.run(
                [sys.executable, "-m", "pytest", str(test_file), "-v", "--tb=short"],
                capture_output=True,
                text=True,
                cwd=self.test_dir.parent,
                timeout=300  # 5分钟超时
            )
            
            success = result.returncode == 0
            stdout = result.stdout
            stderr = result.stderr
            
            return success, stdout, stderr
            
        except subprocess.TimeoutExpired:
            logger.error(f"==liuq debug== 测试超时: {test_file.name}")
            return False, "", "测试执行超时"
        except Exception as e:
            logger.error(f"==liuq debug== 测试执行异常: {test_file.name} - {str(e)}")
            return False, "", str(e)
    
    def run_all_tests(self) -> Dict[str, Dict]:
        """运行所有测试用例"""
        logger.info("==liuq debug== 开始批量运行测试用例")
        
        test_files = self.get_test_case_files()
        total_tests = len(test_files)
        passed_tests = 0
        failed_tests = 0
        
        for i, test_file in enumerate(test_files, 1):
            logger.info(f"==liuq debug== 进度: {i}/{total_tests} - {test_file.name}")
            
            success, stdout, stderr = self.run_single_test(test_file)
            
            # 记录结果
            self.results[test_file.name] = {
                'success': success,
                'stdout': stdout,
                'stderr': stderr,
                'file_path': str(test_file)
            }
            
            if success:
                passed_tests += 1
                logger.info(f"==liuq debug== ✓ 通过: {test_file.name}")
            else:
                failed_tests += 1
                logger.error(f"==liuq debug== ✗ 失败: {test_file.name}")
                if stderr:
                    logger.error(f"==liuq debug== 错误信息: {stderr[:200]}...")
        
        # 输出总结
        logger.info("==liuq debug== " + "="*50)
        logger.info(f"==liuq debug== 测试总结:")
        logger.info(f"==liuq debug== 总计: {total_tests}")
        logger.info(f"==liuq debug== 通过: {passed_tests}")
        logger.info(f"==liuq debug== 失败: {failed_tests}")
        logger.info(f"==liuq debug== 成功率: {passed_tests/total_tests*100:.1f}%")
        logger.info("==liuq debug== " + "="*50)
        
        return self.results
    
    def generate_report(self) -> str:
        """生成测试报告"""
        report_lines = []
        report_lines.append("# FastMapV2 测试用例执行报告")
        report_lines.append("")
        report_lines.append(f"执行时间: {self._get_current_time()}")
        report_lines.append("")
        
        # 统计信息
        total = len(self.results)
        passed = sum(1 for r in self.results.values() if r['success'])
        failed = total - passed
        
        report_lines.append("## 执行统计")
        report_lines.append(f"- 总计测试用例: {total}")
        report_lines.append(f"- 通过: {passed}")
        report_lines.append(f"- 失败: {failed}")
        report_lines.append(f"- 成功率: {passed/total*100:.1f}%")
        report_lines.append("")
        
        # 详细结果
        report_lines.append("## 详细结果")
        report_lines.append("")
        
        for test_name, result in self.results.items():
            status = "✓ 通过" if result['success'] else "✗ 失败"
            report_lines.append(f"### {test_name}")
            report_lines.append(f"状态: {status}")
            
            if not result['success'] and result['stderr']:
                report_lines.append("```")
                report_lines.append(result['stderr'][:500])  # 限制错误信息长度
                report_lines.append("```")
            
            report_lines.append("")
        
        return "\n".join(report_lines)
    
    def save_report(self, report_content: str):
        """保存测试报告"""
        report_file = self.test_dir / "test_execution_report.md"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        logger.info(f"==liuq debug== 测试报告已保存: {report_file}")
    
    def _get_current_time(self) -> str:
        """获取当前时间字符串"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def main():
    """主函数"""
    logger.info("==liuq debug== FastMapV2 测试用例批量运行器启动")
    
    runner = TestCaseRunner()
    
    # 运行所有测试
    results = runner.run_all_tests()
    
    # 生成并保存报告
    report = runner.generate_report()
    runner.save_report(report)
    
    # 输出简要结果
    total = len(results)
    passed = sum(1 for r in results.values() if r['success'])
    
    if passed == total:
        logger.info("==liuq debug== 🎉 所有测试用例都通过了！")
        return 0
    else:
        logger.warning(f"==liuq debug== ⚠️ 有{total-passed}个测试用例失败")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
