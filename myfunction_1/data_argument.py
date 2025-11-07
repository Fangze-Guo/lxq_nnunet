import os
import nibabel as nib
import numpy as np
from tqdm import tqdm

def create_output_dir_structure(base_path):
    """创建与原始目录结构相同的输出目录"""
    output_base = base_path + "_enhanced"
    os.makedirs(output_base, exist_ok=True)
    
    # 创建所有子目录
    for root, dirs, files in os.walk(base_path):
        # 计算相对路径
        rel_path = os.path.relpath(root, base_path)
        output_dir = os.path.join(output_base, rel_path)
        
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
    
    return output_base

def enhance_image(image_path, output_path, contrast_factor=1.5, brightness_factor=0.1):
    """
    增强图像的对比度和亮度并保存到新路径
    :param image_path: 输入图像路径
    :param output_path: 输出图像路径
    :param contrast_factor: 对比度增强因子
    :param brightness_factor: 亮度增强因子
    """
    try:
        # 加载图像
        img = nib.load(image_path)
        data = img.get_fdata()
        affine = img.affine
        header = img.header
        
        # 保存原始数据类型
        orig_dtype = data.dtype
        
        # 转换为float32进行处理
        data = data.astype(np.float32)
        
        # 归一化到0-1范围
        data_min = np.min(data)
        data_max = np.max(data)
        data_range = data_max - data_min
        
        if data_range > 0:  # 避免除以零
            data_normalized = (data - data_min) / data_range
        else:
            data_normalized = data - data_min
        
        # 应用对比度增强
        data_enhanced = np.clip((data_normalized - 0.5) * contrast_factor + 0.5, 0, 1)
        
        # 应用亮度增强
        data_enhanced = np.clip(data_enhanced + brightness_factor, 0, 1)
        
        # 恢复到原始范围并转换回原始数据类型
        data_enhanced = data_enhanced * data_range + data_min
        data_enhanced = data_enhanced.astype(orig_dtype)
        
        # 保存增强后的图像
        enhanced_img = nib.Nifti1Image(data_enhanced, affine, header)
        nib.save(enhanced_img, output_path)
        
    except Exception as e:
        print(f"处理文件 {image_path} 时出错: {str(e)}")

def process_dataset(base_path, contrast_factor=1.5, brightness_factor=0.1, skip_labels=True):
    """
    处理整个数据集目录结构
    :param base_path: 数据集基础路径
    :param contrast_factor: 对比度增强因子
    :param brightness_factor: 亮度增强因子
    :param skip_labels: 是否跳过标签目录
    """
    # 创建输出目录结构
    output_base = create_output_dir_structure(base_path)
    
    # 遍历原始目录
    for root, dirs, files in os.walk(base_path):
        # 跳过标签目录（如果设置）
        if skip_labels and "labels" in root.lower():
            continue
            
        # 计算输出目录
        rel_path = os.path.relpath(root, base_path)
        output_dir = os.path.join(output_base, rel_path)
        
        # 处理当前目录中的NIfTI文件
        nii_files = [f for f in files if f.endswith('.nii.gz')]
        
        if nii_files:
            print(f"\n正在处理目录: {rel_path}")
            for file in tqdm(nii_files, desc="处理文件"):
                input_path = os.path.join(root, file)
                output_path = os.path.join(output_dir, file)
                enhance_image(input_path, output_path, contrast_factor, brightness_factor)

if __name__ == "__main__":
    # 原始数据集路径
    base_path = "/home/cqc/下载/nnUNet-master/DATASET/nnUNet_raw/Task001_example"
    
    # 增强参数（可根据需要调整）
    contrast_factor = 1.5    # >1 增加对比度，<1 减少对比度
    brightness_factor = 0.1  # 正值增加亮度，负值减少亮度
    
    # 处理数据集
    process_dataset(
        base_path=base_path,
        contrast_factor=contrast_factor,
        brightness_factor=brightness_factor,
        skip_labels=True  # 跳过标签目录
    )
    
    print("\n图像增强处理完成！增强后的数据已保存到:", base_path + "_enhanced")