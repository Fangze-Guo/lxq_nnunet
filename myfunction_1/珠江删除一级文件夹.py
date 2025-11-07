import os
import shutil
from pathlib import Path
from tqdm import tqdm


def process_nested_folders(root_dir):
    """
    遍历所有二级子文件夹，如果二级子文件夹的命名与一级子文件夹相同，
    将二级子文件夹下的内容复制到对应的一级子文件夹下，然后删除二级子文件夹
    
    :param root_dir: 根目录路径
    """
    root_path = Path(root_dir)
    
    # 检查目录是否存在
    if not root_path.exists():
        print(f"错误：目录 {root_dir} 不存在")
        return
    
    # 获取所有一级子文件夹
    first_level_folders = [f for f in root_path.iterdir() if f.is_dir()]
    
    if not first_level_folders:
        print("没有找到一级子文件夹")
        return
    
    processed_count = 0
    error_count = 0
    
    # 遍历所有一级子文件夹
    for first_folder in tqdm(first_level_folders, desc="处理一级文件夹"):
        try:
            # 获取一级子文件夹下的所有二级子文件夹
            second_level_folders = [f for f in first_folder.iterdir() if f.is_dir()]
            
            for second_folder in second_level_folders:
                # 检查二级子文件夹名称是否与一级子文件夹相同
                if second_folder.name == first_folder.name:
                    print(f"发现匹配的文件夹: {first_folder.name} -> {second_folder.name}")
                    
                    # 获取二级子文件夹下的所有内容
                    items_in_second_folder = list(second_folder.iterdir())
                    
                    if not items_in_second_folder:
                        print(f"二级文件夹 {second_folder} 为空，直接删除")
                        second_folder.rmdir()
                        processed_count += 1
                        continue
                    # 将二级子文件夹下的所有内容移动到一级子文件夹
                    for item in items_in_second_folder:
                        target_path = first_folder / item.name
                        
                        # 如果目标路径已存在，先删除
                        if target_path.exists():
                            if target_path.is_file():
                                target_path.unlink()
                            else:
                                shutil.rmtree(target_path)
                        
                        # 移动文件或文件夹
                        if item.is_file():
                            shutil.move(str(item), str(target_path))
                        else:
                            shutil.move(str(item), str(first_folder))
                    
                    # 删除空的二级子文件夹
                    if second_folder.exists() and not any(second_folder.iterdir()):
                        second_folder.rmdir()
                        print(f"已删除空文件夹: {second_folder}")
                    
                    processed_count += 1
                    
        except Exception as e:
            print(f"处理文件夹 {first_folder} 时出错: {e}")
            error_count += 1
    
    print(f"\n处理完成！")
    print(f"总共处理了 {processed_count} 个匹配的二级文件夹")
    print(f"遇到 {error_count} 个错误")


def safe_move_with_overwrite(src, dst):
    """
    安全移动文件或文件夹，如果目标存在则覆盖
    
    :param src: 源路径
    :param dst: 目标路径
    """
    if dst.exists():
        if dst.is_file():
            dst.unlink()
        else:
            shutil.rmtree(dst)
    
    shutil.move(str(src), str(dst))


def main():
    # 设置要处理的根目录
    target_dir = "/media/dell/T7 Shield/nnunet/AllData/珠江医院/命名规范化"
    
    print(f"开始处理目录: {target_dir}")
    print("=" * 50)
    
    # 执行处理
    process_nested_folders(target_dir)
    
    print("=" * 50)
    print("处理完成！")


if __name__ == "__main__":
    main()