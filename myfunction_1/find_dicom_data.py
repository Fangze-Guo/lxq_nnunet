#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用法:
python batch_dcm2excel.py
或（自定义根目录）
python batch_dcm2excel.py /你的/根/目录
"""
import os
import sys
from pathlib import Path
import pandas as pd
import pydicom

# -------- 配置 --------
ROOT_DIR = Path(r'/media/cqc/新加卷/my_data/香港大学深圳医院/HKSZ_PHLF Prediction_40/PHLF Prediction_HKSZ_40')

TAGS = {
    'PatientID'        : '病人ID',
    'PatientName'      : '姓名',
    'PatientBirthDate' : '出生日期',
    'PatientSex'       : '性别',
    'PatientAge'       : '年龄',
    'StudyDate'        : '检查日期',
    'StudyTime'        : '检查时间',
    'StudyInstanceUID' : 'StudyInstanceUID',
    'SeriesInstanceUID': 'SeriesInstanceUID',
    'SeriesDescription': '序列描述',
    'Modality'         : '设备类型',
    'Manufacturer'     : '厂商',
    'SliceThickness'   : '层厚(mm)',
    'PixelSpacing'     : '像素间距',
}

# -------- 工具函数 --------
def first_dcm(folder):
    """返回目录下第一张 .dcm 文件路径"""
    for ext in ('*.dcm', '*.ima', '*.DCM'):
        files = list(Path(folder).glob(ext))
        if files:
            return str(files[0])
    return None

def extract_one(folder):
    """从该序列里提取信息"""
    dcm_path = first_dcm(folder)
    if not dcm_path:
        return None
    try:
        ds = pydicom.dcmread(dcm_path, stop_before_pixels=True)
    except Exception as e:
        print(f'[跳过] 无法读取 {dcm_path}: {e}')
        return None

    info = {'序列路径': str(folder)}
    for tag_key, col in TAGS.items():
        elem = ds.get(tag_key)
        if elem is None:
            info[col] = None
            continue
        if hasattr(elem, 'value'):
            val = elem.value
        else:
            val = elem        # 说明它已经是一个普通值
        # 处理常见类型
        if tag_key == 'PatientName':
            val = str(val).replace('^', ' ').strip()
        elif 'Date' in tag_key and len(str(val)) == 8:
            val = f'{val[:4]}-{val[4:6]}-{val[6:8]}'
        elif tag_key == 'PixelSpacing':
            val = 'x'.join(f'{float(v):.3f}' for v in val) if isinstance(val, (list, tuple)) else str(val)
        info[col] = val
    return info

def main(root):
    root = Path(root)
    if not root.is_dir():
        print('给出的根目录不存在！')
        sys.exit(1)

    folders = [p for p in root.iterdir() if p.is_dir()]
    if not folders:
        print('根目录下没有子文件夹！')
        sys.exit(1)

    records = []
    for seq_dir in folders:
        rec = extract_one(seq_dir)
        if rec:
            records.append(rec)

    if not records:
        print('未提取到任何信息。')
        return

    df = pd.DataFrame(records)
    out_xlsx = root.with_name('patient_summary.xlsx')
    df.to_excel(out_xlsx, index=False, engine='openpyxl')
    print(f'[完成] 已生成 {out_xlsx}，共 {len(df)} 条记录。')

if __name__ == '__main__':
    rd = sys.argv[1] if len(sys.argv) > 1 else ROOT_DIR
    main(rd)