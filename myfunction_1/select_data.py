import os
import pandas as pd

# 设置路径
nii_folder = "/media/cqc/新加卷/my_data/NFYShZh/seg_2/muscle"
excel_file = "/media/cqc/新加卷/my_data/NFYShZh/raw_data_nii/select.xlsx"

# 获取所有.nii.gz文件名（去掉 .nii.gz 并去除前导零）
nii_files = [
    f.replace('.nii.gz', '').lstrip('0')
    for f in os.listdir(nii_folder)
    if f.endswith('.nii.gz')
]

# 从Excel读取PatientID列，并去除前导零
try:
    df = pd.read_excel(excel_file)
    patient_ids = df['PatientID'].astype(str).str.lstrip('0').tolist()
except Exception as e:
    print(f"读取Excel文件出错: {e}")
    exit()

# 找出未匹配的文件（原始文件名）
missing_files = [
    f for f in os.listdir(nii_folder)
    if f.endswith('.nii.gz')
    and f.replace('.nii.gz', '').lstrip('0') not in patient_ids
]

# 删除未匹配的文件
if missing_files:
    print("以下文件将被删除（未在PatientID中出现）：")
    for file in missing_files:
        file_path = os.path.join(nii_folder, file)
        print(f"删除: {file_path}")
        os.remove(file_path)  # 删除文件
    print(f"已删除 {len(missing_files)} 个文件。")
else:
    print("没有需要删除的文件。")