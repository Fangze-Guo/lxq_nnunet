import os
import shutil
from pathlib import Path
import time  # 添加time模块用于延时

def selective_copy():
    # 定义路径
    source_dir = Path("/media/dell/T7 Shield/nnunet/AllData/GXYF/原始数据")
    target_dir = Path("/media/dell/T7 Shield/nnunet/AllData/GXYF/分组数据/1_组1")
    reference_dir = Path("/media/dell/T7 Shield/nnunet/AllData/GXYF/分组数据/precontrast/1_组1_pre")
    
    # 确保目标目录存在
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # 获取参考目录中的所有子文件夹名称
    reference_folders = []
    for item in reference_dir.iterdir():
        if item.is_dir():
            reference_folders.append(item.name)
    
    print(f"找到 {len(reference_folders)} 个参考文件夹:")
    for folder in reference_folders:
        print(f"  - {folder}")
    # 复制匹配的文件夹
    copied_count = 0
    batch_size = 30  # 每批处理的文件夹数量
    sleep_time = 20  # 休息时间（秒）
    for i, folder_name in enumerate(reference_folders, 1):
        source_folder = source_dir / folder_name
        target_folder = target_dir / folder_name
        
        if source_folder.exists() and source_folder.is_dir():
            print(f"[{i}/{len(reference_folders)}] 正在复制: {folder_name}")
            
            # 如果目标文件夹已存在，先删除
            if target_folder.exists():
                shutil.rmtree(target_folder)
            
            # 复制整个文件夹
            shutil.copytree(source_folder, target_folder)
            copied_count += 1
            print(f"✓ 成功复制: {folder_name}")
        else:
            print(f"[{i}/{len(reference_folders)}] ✗ 源文件夹不存在: {folder_name}")
        
        # 每复制30个文件夹后休息20秒
        if i % batch_size == 0 and i < len(reference_folders):
            print(f"\n已完成 {i} 个文件夹的复制，休息 {sleep_time} 秒...")
            time.sleep(sleep_time)
            print("休息结束，继续复制...")
    
    print(f"\n复制完成! 成功复制 {copied_count} 个文件夹")

if __name__ == "__main__":
    selective_copy()