import os
import numpy as np
from pathlib import Path

def check_dataset_structure(dataset_path):
    """
    检查数据集目录结构
    """
    dataset_path = Path(dataset_path)
    print(f"检查数据集目录: {dataset_path}")
    print("-" * 50)
    
    # 检查imagesTr目录
    images_tr = dataset_path / "imagesTr"
    if images_tr.exists():
        nifti_files = list(images_tr.glob("*.nii.gz"))
        print(f"imagesTr 中的 .nii.gz 文件数量: {len(nifti_files)}")
        if nifti_files:
            print("前5个文件:")
            for f in nifti_files[:5]:
                print(f"  - {f.name}")
    else:
        print("❌ imagesTr 目录不存在")
        return False
    
    # 检查labelsTr目录
    labels_tr = dataset_path / "labelsTr"
    if labels_tr.exists():
        nifti_files = list(labels_tr.glob("*.nii.gz"))
        print(f"labelsTr 中的 .nii.gz 文件数量: {len(nifti_files)}")
        if nifti_files:
            print("前5个文件:")
            for f in nifti_files[:5]:
                print(f"  - {f.name}")
    else:
        print("❌ labelsTr 目录不存在")
        return False
    
    return True

def check_file_correspondence(images_dir, labels_dir):
    """
    检查两个目录中的文件对应关系
    """
    images_path = Path(images_dir)
    labels_path = Path(labels_dir)
    
    # 获取所有nii.gz文件
    image_files = {f.stem.split('.')[0] for f in images_path.glob("*.nii.gz")}
    label_files = {f.stem.split('.')[0] for f in labels_path.glob("*.nii.gz")}
    
    print(f"\n图像文件数量: {len(image_files)}")
    print(f"标签文件数量: {len(label_files)}")
    
    # 检查对应关系
    only_in_images = image_files - label_files
    only_in_labels = label_files - image_files
    common_files = image_files & label_files
    
    print(f"\n共同文件数量: {len(common_files)}")
    print(f"只在图像中的文件: {len(only_in_images)}")
    print(f"只在标签中的文件: {len(only_in_labels)}")
    
    if only_in_images:
        print("\n只在图像目录中存在的文件:")
        for f in sorted(only_in_images)[:10]:  # 只显示前10个
            print(f"  - {f}")
        if len(only_in_images) > 10:
            print(f"  - ... 还有 {len(only_in_images) - 10} 个文件")
    
    if only_in_labels:
        print("\n只在标签目录中存在的文件:")
        for f in sorted(only_in_labels)[:10]:
            print(f"  - {f}")
        if len(only_in_labels) > 10:
            print(f"  - ... 还有 {len(only_in_labels) - 10} 个文件")
    
    return common_files, only_in_images, only_in_labels

def check_dataset_json(dataset_path):
    """
    检查dataset.json文件
    """
    dataset_json = Path(dataset_path) / "dataset.json"
    if dataset_json.exists():
        print(f"\n✅ dataset.json 文件存在")
        # 您可以添加代码来解析和检查dataset.json内容
        return True
    else:
        print(f"\n❌ dataset.json 文件不存在")
        return False

def main():
    dataset_path = "/home/cqc/下载/nnUNet-master/DATASET/nnUNet_raw/Dataset001_example"
    images_dir = os.path.join(dataset_path, "imagesTr")
    labels_dir = os.path.join(dataset_path, "labelsTr")
    
    print("=" * 60)
    print("nnUNet 数据集完整性检查")
    print("=" * 60)
    
    # 检查目录结构
    if not check_dataset_structure(dataset_path):
        return
    
    # 检查文件对应关系
    common_files, only_in_images, only_in_labels = check_file_correspondence(images_dir, labels_dir)
    
    # 检查dataset.json
    check_dataset_json(dataset_path)
    
    print("\n" + "=" * 60)
    print("问题诊断:")
    print("=" * 60)
    
    if len(common_files) == 0:
        print("❌ 严重问题: 没有找到任何匹配的图像和标签文件")
        print("可能的原因:")
        print("1. 文件命名不匹配")
        print("2. 文件扩展名不一致")
        print("3. 文件可能在其他目录中")
    elif len(common_files) == 1:
        print("⚠️  只找到1个匹配的文件，但nnUNet期望73个")
        print("可能的原因:")
        print("1. 数据集不完整")
        print("2. 文件命名格式不正确")
        print("3. 文件可能在其他子目录中")
        
        # 显示找到的那个文件
        if common_files:
            print(f"找到的文件: {list(common_files)[0]}")
    else:
        print(f"✅ 找到 {len(common_files)} 个匹配的文件")
        if len(common_files) < 73:
            print(f"⚠️  文件数量 ({len(common_files)}) 少于期望的73个")
    
    # 检查文件命名模式
    print(f"\n检查文件命名模式:")
    image_files = list(Path(images_dir).glob("*.nii.gz"))
    if image_files:
        sample_name = image_files[0].name
        print(f"示例文件名: {sample_name}")
        
        # 检查命名是否符合nnUNet要求
        if "case_" in sample_name:
            print("✅ 文件名包含 'case_' 前缀")
        else:
            print("⚠️  文件名可能不符合nnUNet命名约定")
    
    # 建议的解决方案
    print(f"\n" + "=" * 60)
    print("建议的解决方案:")
    print("=" * 60)
    print("1. 确保 imagesTr 和 labelsTr 目录中有相同数量的文件")
    print("2. 确保对应的图像和标签文件有相同的文件名（不包括扩展名）")
    print("3. 检查 dataset.json 文件中的 'numTraining' 字段是否正确")
    print("4. 确保所有文件都是 .nii.gz 格式")
    print("5. 检查文件命名是否符合 nnUNet 的约定 (如: case_001.nii.gz)")

if __name__ == "__main__":
    main()