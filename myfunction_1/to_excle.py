import os
import pandas as pd

# 指定文件夹路径
folder_path = "/media/cqc/新加卷/my_data/广东省人民医院/Liver_Spleen_Muscle_160/Images_all_T1WI_pre_Water"

# 获取所有.nii.gz文件
nii_files = [f for f in os.listdir(folder_path) if f.endswith('.nii.gz')]

# 创建DataFrame
df = pd.DataFrame(nii_files, columns=['File Name'])

# 保存到Excel文件
output_excel = "/media/cqc/新加卷/my_data/广东省人民医院/Liver_Spleen_Muscle_160/Images_all_T1WI_pre_Water/nii_file_names.xlsx"
df.to_excel(output_excel, index=False)

print(f"成功保存了{len(nii_files)}个文件名到 {output_excel}")