import os
import glob
import numpy as np
import SimpleITK as sitk
from pathlib import Path

def merge_labels_in_files(input_dir, output_dir):
    """
    将每个nii.gz文件中的多个标签合并为一个标签（值为1）
    不改变原始文件，创建新的合并后的文件，保持原文件名
    
    参数:
    input_dir: 输入目录路径
    output_dir: 输出目录路径
    """
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 获取所有的nii.gz文件
    nii_files = sorted(glob.glob(os.path.join(input_dir, "*.nii.gz")))
    
    if not nii_files:
        print(f"在目录 {input_dir} 中没有找到.nii.gz文件")
        return
    
    print(f"找到 {len(nii_files)} 个nii.gz文件")
    
    # 处理每个文件
    for i, file_path in enumerate(nii_files, 1):
        original_filename = os.path.basename(file_path)
        print(f"处理文件 {i}: {original_filename}")
        
        # 读取图像
        image = sitk.ReadImage(file_path)
        array = sitk.GetArrayFromImage(image)
        
        # 将多个标签合并为一个标签（值为1）
        # 将所有非零像素设置为1
        binary_array = (array > 0).astype(np.uint8)
        
        # 创建新的SimpleITK图像
        merged_image = sitk.GetImageFromArray(binary_array)
        merged_image.SetSpacing(image.GetSpacing())
        merged_image.SetOrigin(image.GetOrigin())
        merged_image.SetDirection(image.GetDirection())
        
        # 保存合并后的文件，保持原文件名
        output_filename = os.path.join(output_dir, original_filename)
        sitk.WriteImage(merged_image, output_filename)
        
        print(f"  已保存: {original_filename}")
    
    print(f"所有文件处理完成！输出目录: {output_dir}")

def main():
    # 输入和输出路径
    input_directory = "/media/dell/T7 Shield/nnunet/数据中心/ST/mask/Couinaud_modified_80_STYFY_Du/Couinaud_modified_80"
    output_directory = "/media/dell/T7 Shield/nnunet/数据中心/ST/mask/merged_labels"
    
    # 执行合并
    merge_labels_in_files(input_directory, output_directory)

if __name__ == "__main__":
    main()