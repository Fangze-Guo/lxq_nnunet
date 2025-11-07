import os
import nibabel as nib
import numpy as np
from collections import defaultdict

def analyze_labels(input_dir, output_file=None):
    """
    分析文件夹中所有NIfTI文件的标签值
    参数：
        input_dir: 输入文件夹路径
        output_file: 可选，统计结果输出文件路径
    """
    # 获取所有.nii.gz文件
    nii_files = [f for f in os.listdir(input_dir) if f.endswith('.nii.gz')]
    nii_files.sort()  # 按文件名排序
    
    # 存储统计结果
    label_stats = defaultdict(list)
    all_labels = set()
    
    print("开始分析标签...\n")
    
    # 分析每个文件
    for filename in nii_files:
        filepath = os.path.join(input_dir, filename)
        try:
            # 加载文件
            img = nib.load(filepath)
            data = img.get_fdata()
            
            # 获取唯一标签（排除NaN，转换为整数）
            labels = np.unique(data[~np.isnan(data)]).astype(int)
            labels = sorted(labels)
            
            # 记录结果
            label_stats[tuple(labels)].append(filename)
            all_labels.update(labels)
            
            # 打印当前文件结果
            print(f"{filename}: {labels}")
            
        except Exception as e:
            print(f"分析 {filename} 时出错: {str(e)}")
            continue
    
    # 打印汇总信息
    print("\n===== 标签统计汇总 =====")
    print(f"分析文件总数: {len(nii_files)}")
    print(f"所有唯一标签值: {sorted(all_labels)}")
    
    # 输出到文件（如果指定）
    if output_file:
        with open(output_file, 'w') as f:
            f.write("=== 各文件标签统计 ===\n\n")
            for labels, files in sorted(label_stats.items(), key=lambda x: len(x[1]), reverse=True):
                f.write(f"标签组合 {list(labels)} 出现在 {len(files)} 个文件中:\n")
                f.write("\n".join(f"  {file}" for file in sorted(files)) + "\n\n")
            
            f.write("\n=== 全局统计 ===\n")
            f.write(f"总文件数: {len(nii_files)}\n")
            f.write(f"所有唯一标签值: {sorted(all_labels)}\n")
        
        print(f"\n详细统计已保存到: {output_file}")

# 使用示例
if __name__ == "__main__":
    input_dir = "/media/cqc/新加卷/my_data/广东省人民医院/raw_data/Liver_Spleen_Muscle_160/其他/consecutive_labels"
    output_file = os.path.join(input_dir, "label_statistics_report.txt")
    
    analyze_labels(input_dir, output_file)
