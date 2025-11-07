import os
import pandas as pd

# 定义路径
labels_dir = "/media/dell/T7 Shield/nnunet/AllData/ST/finished/precontrast/3个肝段有问题/precouinaud"
mapping_file = "/media/dell/T7 Shield/nnunet/AllData/ST/finished/precontrast/3个肝段有问题/image.tsv"

# 读取映射文件
mapping_df = pd.read_csv(mapping_file, sep='\t')

# 创建从标准化名称到原始名称的映射字典
# 只需要匹配前9个字符（case_000x）
name_mapping = {row['standardized_name'][:9]: row['original_name'] for _, row in mapping_df.iterrows()}

# 遍历labelsTs目录中的所有文件
for filename in os.listdir(labels_dir):
    if filename.endswith('.nii.gz'):
        # 获取文件名的前9个字符作为键

        key = filename[:9]
        
        # 如果在映射字典中找到匹配项
        if key in name_mapping:
            original_name = name_mapping[key]
            old_path = os.path.join(labels_dir, filename)
            new_path = os.path.join(labels_dir, original_name)
            
            # 重命名文件
            os.rename(old_path, new_path)
            print(f"Renamed: {filename} -> {original_name}")

print("File renaming completed.")