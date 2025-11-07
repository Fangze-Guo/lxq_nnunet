import os
import shutil
from pathlib import Path

def copy_second_level_subfolders(source_dir, target_dir):
    """
    将源目录中的所有二级子文件夹复制到目标目录
    
    参数:
    source_dir: 源目录路径
    target_dir: 目标目录路径
    """
    # 转换为Path对象
    source_path = Path(source_dir)
    target_path = Path(target_dir)
    
    # 确保目标目录存在
    target_path.mkdir(parents=True, exist_ok=True)
    
    # 检查源目录是否存在
    if not source_path.exists():
        print(f"错误: 源目录不存在: {source_path}")
        return
    
    # 遍历源目录的第一级子目录
    for first_level in source_path.iterdir():
        if first_level.is_dir():
            # 遍历第二级子目录
            for second_level in first_level.iterdir():
                if second_level.is_dir():
                    # 构建目标路径
                    target_subdir = target_path / second_level.name
                    
                    # 如果目标目录已存在，先删除
                    if target_subdir.exists():
                        shutil.rmtree(target_subdir)
                        print(f"已删除现有目录: {target_subdir}")
                    
                    # 复制目录
                    try:
                        shutil.copytree(second_level, target_subdir)
                        print(f"成功复制: {second_level} -> {target_subdir}")
                    except Exception as e:
                        print(f"复制失败 {second_level}: {e}")

if __name__ == "__main__":
    # 设置源目录和目标目录
    source_directory = "/media/dell/T7 Shield/nnunet/数据中心/北大深圳/原始数据"
    target_directory = "/media/dell/T7 Shield/nnunet/数据中心/北大深圳/副本"
    
    print("开始复制二级子文件夹...")
    print(f"源目录: {source_directory}")
    print(f"目标目录: {target_directory}")
    print("-" * 50)
    
    copy_second_level_subfolders(source_directory, target_directory)
    
    print("-" * 50)
    print("复制操作完成!")