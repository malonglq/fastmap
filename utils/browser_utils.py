#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
浏览器相关工具
==liuq debug== 统一在Windows上使用系统默认浏览器打开本地HTML报告，确保路径与协议正确

提供函数：
- open_html_report(file_path): 打开本地HTML报告（推荐）
- open_in_default_browser(file_path): 别名
"""
from pathlib import Path
import logging
import os
import webbrowser
from typing import Union

logger = logging.getLogger(__name__)


def _to_file_uri(file_path: Union[str, Path]) -> str:
    """将本地路径转换为绝对 file URI（file:///C:/...）"""
    p = Path(file_path).resolve()
    return p.as_uri()


def open_html_report(file_path: Union[str, Path]) -> bool:
    """
    在系统默认浏览器中打开本地HTML报告（Windows优先）。

    策略：
    1) 构造绝对 file URI
    2) 优先 webbrowser.get('windows-default').open_new_tab(url)
    3) 失败回退 os.startfile(abs_path)
    4) 最后回退 webbrowser.open(url)

    返回：bool 是否认为已成功触发打开
    """
    try:
        p = Path(file_path).resolve()
        url = p.as_uri()
        logger.info(f"==liuq debug== 准备打开报告: path={p} url={url}")
        try:
            # Windows 默认浏览器
            b = webbrowser.get('windows-default')
            ok = b.open_new_tab(url)
            logger.info(f"==liuq debug== windows-default 打开结果: {ok}")
            if ok:
                return True
        except Exception as e:
            logger.warning(f"==liuq debug== windows-default 打开失败: {e}")

        # 回退1：按 .html 关联打开
        try:
            if os.name == 'nt':
                os.startfile(str(p))  # type: ignore[attr-defined]
                logger.info("==liuq debug== os.startfile 已触发")
                return True
        except Exception as e2:
            logger.warning(f"==liuq debug== os.startfile 打开失败: {e2}")

        # 回退2：通用方式
        try:
            ok2 = webbrowser.open(url)
            logger.info(f"==liuq debug== webbrowser.open 回退结果: {ok2}")
            return bool(ok2)
        except Exception as e3:
            logger.error(f"==liuq debug== webbrowser.open 也失败: {e3}")
            return False

    except Exception as e:
        logger.error(f"==liuq debug== open_html_report 总体失败: {e}")
        return False


# 别名，便于更通用的调用命名
open_in_default_browser = open_html_report

