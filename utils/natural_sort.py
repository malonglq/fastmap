"""
自然数排序工具模块

提供自然数排序功能，能够正确处理包含数字的字符串排序。
例如：["item1", "item11", "item2", "item21"] -> ["item1", "item2", "item11", "item21"]

设计特点：
- 支持多种数字模式的字符串排序
- 保持非数字部分的字符串排序
- 提供通用的排序函数和比较函数
- 支持自定义排序键提取
"""

import re
import logging
from typing import List, Any, Callable, Optional, Union

logger = logging.getLogger(__name__)


def extract_natural_sort_key(text: str) -> List[Union[int, str]]:
    """
    提取自然排序键
    
    将字符串分解为数字和非数字部分的列表，用于自然排序比较。
    
    Args:
        text: 要处理的字符串
        
    Returns:
        包含数字（int）和字符串（str）的列表
        
    Examples:
        >>> extract_natural_sort_key("offset_map2")
        ['offset_map', 2]
        >>> extract_natural_sort_key("item10_sub3")
        ['item', 10, '_sub', 3]
        >>> extract_natural_sort_key("abc")
        ['abc']
    """
    try:
        # 使用正则表达式分割数字和非数字部分
        parts = re.split(r'(\d+)', str(text))
        
        # 转换数字部分为整数，保持字符串部分不变
        result = []
        for part in parts:
            if part.isdigit():
                result.append(int(part))
            elif part:  # 忽略空字符串
                result.append(part)
        
        return result
        
    except Exception as e:
        logger.warning(f"==liuq debug== 提取自然排序键失败: {text} - {e}")
        # 出错时返回原字符串
        return [str(text)]


def natural_sort_key(item: Any, key_func: Optional[Callable[[Any], str]] = None) -> List[Union[int, str]]:
    """
    生成自然排序键
    
    Args:
        item: 要排序的项目
        key_func: 可选的键提取函数，用于从复杂对象中提取排序字符串
        
    Returns:
        自然排序键列表
        
    Examples:
        >>> natural_sort_key("offset_map2")
        ['offset_map', 2]
        >>> natural_sort_key({"name": "item10"}, lambda x: x["name"])
        ['item', 10]
    """
    try:
        # 提取排序字符串
        if key_func:
            sort_string = key_func(item)
        else:
            sort_string = str(item)
        
        return extract_natural_sort_key(sort_string)
        
    except Exception as e:
        logger.warning(f"==liuq debug== 生成自然排序键失败: {item} - {e}")
        # 出错时返回原字符串
        return [str(item)]


def natural_sort(items: List[Any], key_func: Optional[Callable[[Any], str]] = None, reverse: bool = False) -> List[Any]:
    """
    自然数排序函数
    
    对包含数字的字符串进行自然排序，数字部分按数值大小排序。
    
    Args:
        items: 要排序的项目列表
        key_func: 可选的键提取函数，用于从复杂对象中提取排序字符串
        reverse: 是否降序排序
        
    Returns:
        排序后的列表
        
    Examples:
        >>> natural_sort(["item1", "item11", "item2", "item21"])
        ['item1', 'item2', 'item11', 'item21']
        >>> natural_sort(["offset_map1", "offset_map11", "offset_map2"])
        ['offset_map1', 'offset_map2', 'offset_map11']
    """
    try:

        
        # 使用自然排序键进行排序
        sorted_items = sorted(items, key=lambda x: natural_sort_key(x, key_func), reverse=reverse)
        

        return sorted_items
        
    except Exception as e:
        logger.error(f"==liuq debug== 自然排序失败: {e}")
        # 出错时返回原列表
        return items.copy()


def compare_natural(a: str, b: str) -> int:
    """
    自然排序比较函数
    
    比较两个字符串的自然排序顺序。
    
    Args:
        a: 第一个字符串
        b: 第二个字符串
        
    Returns:
        -1 if a < b, 0 if a == b, 1 if a > b
        
    Examples:
        >>> compare_natural("item2", "item10")
        -1
        >>> compare_natural("item10", "item2")
        1
        >>> compare_natural("item2", "item2")
        0
    """
    try:
        key_a = extract_natural_sort_key(a)
        key_b = extract_natural_sort_key(b)
        
        if key_a < key_b:
            return -1
        elif key_a > key_b:
            return 1
        else:
            return 0
            
    except Exception as e:
        logger.warning(f"==liuq debug== 自然排序比较失败: {a} vs {b} - {e}")
        # 出错时使用普通字符串比较
        if a < b:
            return -1
        elif a > b:
            return 1
        else:
            return 0


class NaturalSortMixin:
    """
    自然排序混入类
    
    为其他类提供自然排序功能的混入类。
    """
    
    def get_natural_sort_key(self, text: str) -> List[Union[int, str]]:
        """获取自然排序键"""
        return extract_natural_sort_key(text)
    
    def natural_sort_list(self, items: List[Any], key_func: Optional[Callable[[Any], str]] = None, reverse: bool = False) -> List[Any]:
        """对列表进行自然排序"""
        return natural_sort(items, key_func, reverse)
    
    def compare_natural_strings(self, a: str, b: str) -> int:
        """比较两个字符串的自然排序顺序"""
        return compare_natural(a, b)


# 测试函数
def test_natural_sort():
    """测试自然排序功能"""
    test_cases = [
        ["item1", "item11", "item2", "item21"],
        ["offset_map1", "offset_map11", "offset_map2", "offset_map116"],
        ["1_BlueSky_Bright", "11_InterferenceColor_Dim", "2_BlueSky_Dim", "21_Indoor_BV_4000"],
        ["file1.txt", "file10.txt", "file2.txt", "file20.txt"],
        ["version1.0", "version1.10", "version1.2", "version2.0"],
    ]
    
    print("==liuq debug== 自然排序测试:")
    for i, test_list in enumerate(test_cases, 1):
        print(f"\n测试用例 {i}:")
        print(f"原始: {test_list}")
        sorted_list = natural_sort(test_list)
        print(f"排序: {sorted_list}")


if __name__ == "__main__":
    test_natural_sort()
