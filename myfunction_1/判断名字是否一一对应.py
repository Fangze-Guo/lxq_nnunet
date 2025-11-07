import os
import argparse

def check_nifti_filename_correspondence(images_dir, labels_dir):
    """
    检查两个目录中的NIfTI文件命名是否一一对应
    
    参数:
        images_dir: 图像文件目录路径
        labels_dir: 标签文件目录路径
        
    返回:
        tuple: (是否完全对应, 缺失的图像文件列表, 缺失的标签文件列表)
    """
    # 获取两个目录中的所有.nii.gz文件
    images_files = {f for f in os.listdir(images_dir) if f.endswith('.nii.gz')}
    labels_files = {f for f in os.listdir(labels_dir) if f.endswith('.nii.gz')}
    
    print(f"图像目录中找到 {len(images_files)} 个.nii.gz文件")
    print(f"标签目录中找到 {len(labels_files)} 个.nii.gz文件")
    
    # 找出只在图像目录中存在的文件
    only_in_images = images_files - labels_files
    
    # 找出只在标签目录中存在的文件
    only_in_labels = labels_files - images_files
    
    # 找出共同的文件
    common_files = images_files & labels_files
    
    # 检查是否完全对应
    is_correspond = len(only_in_images) == 0 and len(only_in_labels) == 0
    
    return is_correspond, only_in_images, only_in_labels, common_files

def main():
    # 设置命令行参数
    parser = argparse.ArgumentParser(description='检查两个目录中的NIfTI文件命名是否一一对应')
    parser.add_argument('images_dir', help='图像文件目录路径')
    parser.add_argument('labels_dir', help='标签文件目录路径')
    
    args = parser.parse_args()
    
    # 检查目录是否存在
    if not os.path.exists(args.images_dir):
        print(f"错误: 图像目录 '{args.images_dir}' 不存在")
        return
    
    if not os.path.exists(args.labels_dir):
        print(f"错误: 标签目录 '{args.labels_dir}' 不存在")
        return
    
    # 检查文件对应性
    is_correspond, only_in_images, only_in_labels, common_files = check_nifti_filename_correspondence(
        args.images_dir, args.labels_dir
    )
    
    # 输出结果
    if is_correspond:
        print("\n✅ 所有文件都一一对应！")
        print(f"共同文件数量: {len(common_files)}")
    else:
        print("\n❌ 文件命名不匹配：")
        
        if only_in_images:
            print(f"\n只在图像目录中存在的文件 ({len(only_in_images)} 个):")
            for file in sorted(only_in_images):
                print(f"  - {file}")
        
        if only_in_labels:
            print(f"\n只在标签目录中存在的文件 ({len(only_in_labels)} 个):")
            for file in sorted(only_in_labels):
                print(f"  - {file}")
        
        print(f"\n共同文件数量: {len(common_files)}")
        
        # 显示一些共同文件作为示例
        if common_files:
            print("\n共同文件示例 (前5个):")
            for file in sorted(list(common_files)[:5]):
                print(f"  - {file}")
            if len(common_files) > 5:
                print(f"  - ... (还有 {len(common_files) - 5} 个文件)")

if __name__ == "__main__":
    # 直接使用提供的路径
    images_path = "DATASET/nnUNet_raw/Task004_example/imagesTr"
    labels_path = "DATASET/nnUNet_raw/Task004_example/labelsTr"
    
    # 检查目录是否存在
    if not os.path.exists(images_path):
        print(f"错误: 图像目录 '{images_path}' 不存在")
        exit(1)
    
    if not os.path.exists(labels_path):
        print(f"错误: 标签目录 '{labels_path}' 不存在")
        exit(1)
    
    # 检查文件对应性
    print(f"检查目录:")
    print(f"  图像: {images_path}")
    print(f"  标签: {labels_path}")
    print("-" * 50)
    
    is_correspond, only_in_images, only_in_labels, common_files = check_nifti_filename_correspondence(
        images_path, labels_path
    )
    
    # 输出结果
    if is_correspond:
        print("\n✅ 所有文件都一一对应！")
        print(f"共同文件数量: {len(common_files)}")
    else:
        print("\n❌ 文件命名不匹配：")
        
        if only_in_images:
            print(f"\n只在图像目录中存在的文件 ({len(only_in_images)} 个):")
            for file in sorted(only_in_images):
                print(f"  - {file}")
        
        if only_in_labels:
            print(f"\n只在标签目录中存在的文件 ({len(only_in_labels)} 个):")
            for file in sorted(only_in_labels):
                print(f"  - {file}")
        
        print(f"\n共同文件数量: {len(common_files)}")
        
        # 显示一些共同文件作为示例
        if common_files:
            print("\n共同文件示例 (前5个):")
            for file in sorted(list(common_files)[:5]):
                print(f"  - {file}")
            if len(common_files) > 5:
                print(f"  - ... (还有 {len(common_files) - 5} 个文件)")
