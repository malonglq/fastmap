import ctypes as C
import os
import win32api
import json
import csv
from ctypes import c_void_p, byref
from datetime import datetime

handle = C.c_void_p(None)

def InitDLL():
    lib_path = './dll/Release/3a_parser.dll'
    global lib
    lib = C.cdll.LoadLibrary(lib_path)
    InitFunc = lib.init
    InitFunc.argtypes = [C.POINTER(C.c_void_p)]
    InitFunc.restype = None
    global handle
    InitFunc(byref(handle))
    if handle is not None:
        print('Load and init Lib success')
    else:
        print('Load and init Lib failed')

def getAfExifData(file_path):
    getAfExifFunc = lib.getAfExifJson
    getAfExifFunc.argtypes = [C.c_void_p, C.c_char_p, C.c_bool]
    getAfExifFunc.restype = C.c_char_p
    in_str = C.c_char_p(file_path.encode())
    out_str = getAfExifFunc(handle, in_str, C.c_bool(False))
    AFMetadataString = str(out_str, encoding='utf-8')
    return AFMetadataString

def getAecExifData(file_path):
    getAecExifFunc = lib.getAecExifJson
    getAecExifFunc.argtypes = [C.c_void_p, C.c_char_p, C.c_bool]
    getAecExifFunc.restype = C.c_char_p
    in_str = C.c_char_p(file_path.encode())
    out_str = getAecExifFunc(handle, in_str, C.c_bool(False))
    AEMetadataString = str(out_str, encoding='utf-8')
    return AEMetadataString

def getAwbExifData(file_path, exif=None, is_reverse=False, enable_save=False):
    """
    解析AwbExif的接口
    参数：
    file_path: 图片路径
    exif: AwbExifInfo结构体，没有就传None
    is_reverse: 控制从数据头还是尾开始查找标志位，False为从头查找
    enable_save: 控制是否保存json文件的开关
    返回值：解析出来的json字符串
    """
    getAwbExifFunc = lib.getAwbExifJson
    getAwbExifFunc.argtypes = [C.c_void_p, C.c_char_p, C.c_char_p, C.c_bool, C.c_bool]
    getAwbExifFunc.restype = C.c_char_p

    in_str = C.c_char_p(file_path.encode())
    exif_ptr = None if exif is None else C.c_char_p(exif.encode() if isinstance(exif, str) else exif)

    out_str = getAwbExifFunc(handle, in_str, exif_ptr, C.c_bool(is_reverse), C.c_bool(enable_save))
    AWBMetadataString = str(out_str, encoding='utf-8')
    return AWBMetadataString

def writeAwbExifToCsv(file_path, csv_file_path='awb_exif_data.csv', exif=None, is_reverse=False, enable_save=False):
    """
    获取AWB exif数据并写入CSV文件
    参数：
    file_path: 图片路径
    csv_file_path: CSV文件保存路径
    exif: AwbExifInfo结构体，没有就传None
    is_reverse: 控制从数据头还是尾开始查找标志位，False为从头查找
    enable_save: 控制是否保存json文件的开关
    """
    try:
        # 获取AWB exif数据
        awb_json_str = getAwbExifData(file_path, exif, is_reverse, enable_save)

        # 解析JSON数据
        awb_data = json.loads(awb_json_str)

        # 准备CSV数据
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        image_name = os.path.basename(file_path)

        # 检查CSV文件是否存在，如果不存在则创建并写入表头
        file_exists = os.path.exists(csv_file_path)

        with open(csv_file_path, 'a', newline='', encoding='utf-8-sig') as csvfile:
            # 动态获取所有字段名
            fieldnames = ['timestamp', 'image_name', 'image_path']

            # 递归展开JSON数据的所有字段
            def flatten_dict(d, parent_key='', sep='_'):
                items = []
                for k, v in d.items():
                    new_key = f"{parent_key}{sep}{k}" if parent_key else k
                    if isinstance(v, dict):
                        items.extend(flatten_dict(v, new_key, sep=sep).items())
                    else:
                        items.append((new_key, v))
                return dict(items)

            flattened_data = flatten_dict(awb_data)
            fieldnames.extend(flattened_data.keys())

            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            # 如果文件不存在，写入表头
            if not file_exists:
                writer.writeheader()

            # 准备行数据
            row_data = {
                'timestamp': timestamp,
                'image_name': image_name,
                'image_path': file_path
            }
            row_data.update(flattened_data)

            # 写入数据行
            writer.writerow(row_data)

        print(f"==liuq debug== AWB exif数据已成功写入CSV文件: {csv_file_path}")
        return True

    except json.JSONDecodeError as e:
        print(f"==liuq debug== JSON解析错误: {e}")
        print(f"==liuq debug== 原始数据: {awb_json_str}")
        return False
    except Exception as e:
        print(f"==liuq debug== 写入CSV文件时发生错误: {e}")
        return False

def DeInitDLL():
    DeInitFunc = lib.deInit
    DeInitFunc.argtypes = [C.c_void_p]
    DeInitFunc.restype = None
    DeInitFunc(handle)
    win32api.FreeLibrary(lib._handle)
    print('Free Lib')


InitDLL()
d = getAfExifData('./32_zhufeng_IMG20250101194241_ori.jpg')
#print("AF Exif Data:")
#print(d)
d = getAecExifData('./32_zhufeng_IMG20250101194241_ori.jpg')
#print("AEC Exif Data:")
#print(d)
d = getAwbExifData('./32_zhufeng_IMG20250101194241_ori.jpg')
print("AWB Exif Data:")
print(d)

# 将AWB exif数据写入CSV文件
print("\n==liuq debug== 开始将AWB exif数据写入CSV文件...")
success = writeAwbExifToCsv('./32_zhufeng_IMG20250101194241_ori.jpg', 'zf_awb_exif_data.csv')
if success:
    print("==liuq debug== CSV文件写入成功！")
else:
    print("==liuq debug== CSV文件写入失败！")

DeInitDLL()

os.system('pause')
