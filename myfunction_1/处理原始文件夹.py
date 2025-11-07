import os
import shutil
from pathlib import Path

def reorganize_files_and_folders(root_dir):
    """
    将二级子文件夹中的所有内容（文件和文件夹）移动到一级子文件夹，然后删除二级子文件夹
    """
    root_path = Path(root_dir)
    
    # 检查根目录是否存在
    if not root_path.exists():
        print(f"错误：目录 '{root_dir}' 不存在")
        return
    
    # 遍历一级子文件夹
    for first_level in root_path.iterdir():
        if first_level.is_dir():
            print(f"处理一级文件夹: {first_level.name}")
            
            # 遍历二级子文件夹
            for second_level in first_level.iterdir():
                if second_level.is_dir():
                    print(f"  处理二级文件夹: {second_level.name}")
                    
                    # 移动二级文件夹中的所有内容（文件和文件夹）到一级文件夹
                    moved_count = 0
                    for item in second_level.iterdir():
                        # 构建目标路径
                        target_path = first_level / item.name
                        
                        # 如果目标已存在，添加前缀避免冲突
                        if target_path.exists():
                            if item.is_file():
                                new_name = f"{second_level.name}_{item.name}"
                            else:
                                new_name = f"{second_level.name}_{item.name}"
                            target_path = first_level / new_name
                        
                        # 移动项目
                        try:
                            shutil.move(str(item), str(target_path))
                            moved_count += 1
                            if item.is_file():
                                print(f"    移动文件: {item.name} -> {target_path.name}")
                            else:
                                print(f"    移动文件夹: {item.name} -> {target_path.name}")
                        except Exception as e:
                            print(f"    错误移动 {item.name}: {e}")
                    
                    # 检查二级文件夹是否为空，然后删除
                    try:
                        if not any(second_level.iterdir()):
                            second_level.rmdir()
                            print(f"    删除空的二级文件夹: {second_level.name}")
                        else:
                            print(f"    警告：二级文件夹 {second_level.name} 不为空，无法删除")
                    except Exception as e:
                        print(f"    错误删除文件夹 {second_level.name}: {e}")
                    
                    print(f"    共移动 {moved_count} 个项目")
    
    print("操作完成！")

def preview_operations(root_dir):
    """
    预览将要执行的操作，但不实际执行
    """
    root_path = Path(root_dir)
    
    if not root_path.exists():
        print(f"错误：目录 '{root_dir}' 不存在")
        return
    
    print("预览操作：")
    print("=" * 60)
    
    total_operations = 0
    
    for first_level in root_path.iterdir():
        if first_level.is_dir():
            print(f"\n一级文件夹: {first_level.name}")
            
            for second_level in first_level.iterdir():
                if second_level.is_dir():
                    print(f"  └─ 二级文件夹: {second_level.name}")
                    
                    file_count = 0
                    folder_count = 0
                    for item in second_level.iterdir():
                        target_path = first_level / item.name
                        if target_path.exists():
                            if item.is_file():
                                new_name = f"{second_level.name}_{item.name}"
                            else:
                                new_name = f"{second_level.name}_{item.name}"
                            target_path = first_level / new_name
                        
                        if item.is_file():
                            print(f"     移动文件: {item.name} -> {target_path.name}")
                            file_count += 1
                        else:
                            print(f"     移动文件夹: {item.name} -> {target_path.name}")
                            folder_count += 1
                    
                    print(f"     共 {file_count} 个文件, {folder_count} 个文件夹")
                    total_operations += file_count + folder_count
                    print(f"     然后删除二级文件夹: {second_level.name}")
    
    print(f"\n总计: {total_operations} 个操作")
    print("预览完成，以上是将会执行的操作")

if __name__ == "__main__":
    root_directory = "/media/dell/T7 Shield/nnunet/数据中心/北大深圳/原始数据"
    
    # 先预览操作
    preview_operations(root_directory)
    
    # 确认后执行实际操作
    confirm = input("\n是否执行实际操作？(y/n): ")
    if confirm.lower() == 'y':
        print("\n开始执行实际操作...")
        reorganize_files_and_folders(root_directory)
    else:
        print("操作已取消")