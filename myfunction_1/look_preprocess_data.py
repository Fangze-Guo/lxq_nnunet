import os
import glob

def rename_nii_in_subfolders(root_dir, name_mapping):
    """
    对每个子文件夹内的.nii.gz文件执行独立重命名
    
    参数:
        root_dir: 包含多个子文件夹的根目录
        name_mapping: 字典格式 {子文件夹名: 新文件名}
    """
    print("="*50)
    print(f"开始处理目录: {root_dir}")
    print(f"命名规则: {name_mapping}")
    print("="*50)
    
    for subdir, new_name in name_mapping.items():
        subdir_path = os.path.join(root_dir, subdir)
        
        # 检查子文件夹是否存在
        if not os.path.isdir(subdir_path):
            print(f"⚠️ 跳过: 子文件夹 {subdir} 不存在")
            continue
            
        # 查找.nii.gz文件
        nii_files = glob.glob(os.path.join(subdir_path, "*.nii.gz"))
        
        if not nii_files:
            print(f"⚠️ 跳过: {subdir} 中没有找到.nii.gz文件")
            continue
            
        if len(nii_files) > 1:
            print(f"⚠️ 注意: {subdir} 中有多个.nii.gz文件，将处理第一个")
            
        # 执行重命名
        old_path = nii_files[0]
        new_path = os.path.join(subdir_path, f"{new_name}.nii.gz")
        os.rename(old_path, new_path)
        print(f"✅ {subdir}: {os.path.basename(old_path)} -> {new_name}.nii.gz")

if __name__ == "__main__":
    # 配置路径和命名规则
    root_directory = "/media/cqc/新加卷/my_data/HK/seg_2_three"
    
    # 子文件夹名与新文件名的映射关系
    naming_rules = {
        "subfolder1": "AF9975339",  # 子文件夹1 -> AF9975339.nii.gz
        "subfolder2": "AH9265588",  # 子文件夹2 -> AH9265588.nii.gz
        "subfolder3": "AJ9727736",  # 子文件夹3 -> AJ9727736.nii.gz
        "subfolder4": "AK1234567"   # 子文件夹4 -> AK1234567.nii.gz
    }
    
    rename_nii_in_subfolders(root_directory, naming_rules)
    print("\n🎉 全部操作完成")