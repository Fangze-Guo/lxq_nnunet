import os
import numpy as np
import nibabel as nib
from tqdm import tqdm
import matplotlib.pyplot as plt

def adjust_nifti_contrast(input_path, contrast_factor=1.5, method='linear', clip=True):
    """
    调整NIfTI文件的对比度
    
    参数:
    input_path: 输入文件路径
    contrast_factor: 对比度调整因子（>1增加对比度，<1降低对比度）
    method: 调整方法 'linear', 'gamma', 'histogram'
    clip: 是否将值裁剪到合理范围内
    """
    
    # 检查输入文件是否存在
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"文件不存在: {input_path}")
    
    # 加载NIfTI文件
    img = nib.load(input_path)
    data = img.get_fdata().astype(np.float32)
    affine = img.affine
    header = img.header
    
    original_min = np.min(data)
    original_max = np.max(data)
    original_mean = np.mean(data)
    original_dtype = img.get_data_dtype()
    
    print(f"处理: {os.path.basename(input_path)}")
    print(f"原始范围: [{original_min:.2f}, {original_max:.2f}]")
    print(f"原始均值: {original_mean:.2f}")
    
    # 调整对比度
    if method == 'linear':
        # 线性对比度调整
        adjusted_data = original_mean + contrast_factor * (data - original_mean)
        print(f"线性对比度调整: 因子 {contrast_factor}")
        
    elif method == 'gamma':
        # Gamma校正
        # 先归一化到0-1范围
        data_normalized = (data - original_min) / (original_max - original_min + 1e-8)
        # Gamma校正
        data_gamma = np.power(data_normalized, 1.0 / contrast_factor)
        # 恢复原始范围
        adjusted_data = data_gamma * (original_max - original_min) + original_min
        print(f"Gamma校正: γ = {1.0/contrast_factor:.2f}")
        
    elif method == 'histogram':
        # 基于直方图的对比度拉伸
        p5 = np.percentile(data, 5)  # 5%百分位
        p95 = np.percentile(data, 95)  # 95%百分位
        
        # 拉伸对比度
        adjusted_data = (data - p5) * ((original_max - original_min) / (p95 - p5 + 1e-8)) + original_min
        print(f"直方图拉伸: 5%-95% 百分位")
        
    elif method == 'sigmoid':
        # Sigmoid对比度调整
        data_normalized = (data - original_mean) / (original_std + 1e-8)
        adjusted_data = original_mean + (original_max - original_min) * (1 / (1 + np.exp(-contrast_factor * data_normalized)) - 0.5)
        print(f"Sigmoid对比度调整: 因子 {contrast_factor}")
        
    else:
        raise ValueError("方法必须是 'linear', 'gamma', 'histogram', 或 'sigmoid'")
    
    # 裁剪到合理范围
    if clip:
        adjusted_min = max(original_min * 0.9, np.min(adjusted_data))
        adjusted_max = min(original_max * 1.1, np.max(adjusted_data))
        adjusted_data = np.clip(adjusted_data, adjusted_min, adjusted_max)
    
    # 保持原始数据类型
    adjusted_data = adjusted_data.astype(original_dtype)
    
    adjusted_min = np.min(adjusted_data)
    adjusted_max = np.max(adjusted_data)
    adjusted_mean = np.mean(adjusted_data)
    
    print(f"调整后范围: [{adjusted_min:.2f}, {adjusted_max:.2f}]")
    print(f"调整后均值: {adjusted_mean:.2f}")
    
    # 创建新图像并保存
    new_img = nib.Nifti1Image(adjusted_data, affine, header)
    nib.save(new_img, input_path)
    
    print(f"已保存: {os.path.basename(input_path)}")
    print("-" * 50)
    
    return adjusted_data

def plot_comparison(original_data, adjusted_data, filename):
    """绘制调整前后的对比图"""
    plt.figure(figsize=(12, 5))
    
    # 原始数据直方图
    plt.subplot(1, 2, 1)
    plt.hist(original_data.flatten(), bins=50, alpha=0.7, color='blue')
    plt.title('Original Data Histogram')
    plt.xlabel('Intensity')
    plt.ylabel('Frequency')
    
    # 调整后数据直方图
    plt.subplot(1, 2, 2)
    plt.hist(adjusted_data.flatten(), bins=50, alpha=0.7, color='red')
    plt.title('Adjusted Data Histogram')
    plt.xlabel('Intensity')
    plt.ylabel('Frequency')
    
    plt.tight_layout()
    plt.savefig(f'{filename}_contrast_comparison.png', dpi=150, bbox_inches='tight')
    plt.close()

def process_all_nifti_files(directory, contrast_factor=1.5, method='linear', create_plots=False):
    """
    处理目录中的所有NIfTI文件
    
    参数:
    directory: 目录路径
    contrast_factor: 对比度调整因子
    method: 调整方法
    create_plots: 是否创建对比图
    """
    
    if not os.path.exists(directory):
        print(f"错误: 目录不存在: {directory}")
        return
    
    # 获取所有NIfTI文件
    nifti_files = []
    for file in os.listdir(directory):
        if file.endswith('.nii.gz') or file.endswith('.nii'):
            nifti_files.append(os.path.join(directory, file))
    
    if not nifti_files:
        print("该目录中没有找到NIfTI文件")
        return
    
    print(f"找到 {len(nifti_files)} 个NIfTI文件")
    print(f"对比度调整因子: {contrast_factor}")
    print(f"调整方法: {method}")
    print("=" * 60)
    
    # 处理所有文件
    success_count = 0
    failed_count = 0
    
    for file_path in tqdm(nifti_files, desc="调整对比度"):
        try:
            # 先加载原始数据用于对比
            if create_plots:
                original_img = nib.load(file_path)
                original_data = original_img.get_fdata()
            
            adjusted_data = adjust_nifti_contrast(file_path, contrast_factor, method)
            
            if create_plots:
                # 创建对比图
                filename = os.path.splitext(os.path.splitext(os.path.basename(file_path))[0])[0]
                plot_comparison(original_data, adjusted_data, filename)
            
            success_count += 1
        except Exception as e:
            print(f"处理失败 {os.path.basename(file_path)}: {e}")
            failed_count += 1
    
    print("=" * 60)
    print(f"处理完成! 成功: {success_count}, 失败: {failed_count}")

def batch_contrast_adjustment():
    """批量对比度调整"""
    directory = "/media/dell/T7 Shield/nnunet/AllData/ZJYY/dicom_to_nii"
    
    # 对比度调整参数
    contrast_factor = 1.5    # >1增加对比度，<1降低对比度
    method = 'linear'        # 'linear', 'gamma', 'histogram', 'sigmoid'
    create_plots = False     # 是否创建对比图
    
    print("开始调整NIfTI文件对比度...")
    print(f"目录: {directory}")
    print(f"方法: {method}")
    print(f"因子: {contrast_factor}")
    print("=" * 60)
    
    # 确认操作
    confirm = input(f"确定要调整所有NIfTI文件的对比度吗？(y/N): ")
    if confirm.lower() not in ['y', 'yes']:
        print("操作已取消")
        return
    
    # 处理所有文件
    process_all_nifti_files(directory, contrast_factor, method, create_plots)

def interactive_adjustment():
    """交互式对比度调整"""
    directory = "/media/dell/T7 Shield/nnunet/AllData/ZJYY/dicom_to_nii"
    
    print("交互式对比度调整")
    print("=" * 40)
    
    # 选择调整方法
    print("可用方法:")
    print("1. linear - 线性对比度调整")
    print("2. gamma - Gamma校正")
    print("3. histogram - 直方图拉伸")
    print("4. sigmoid - Sigmoid调整")
    
    method_choice = input("选择调整方法 (1-4, 默认1): ").strip()
    methods = ['linear', 'gamma', 'histogram', 'sigmoid']
    method = methods[int(method_choice) - 1] if method_choice and method_choice in '1234' else 'linear'
    
    # 输入调整因子
    try:
        factor = float(input("输入调整因子 (默认1.5): ") or "1.5")
    except ValueError:
        factor = 1.5
    
    create_plots = input("是否创建对比图？(y/N): ").lower() in ['y', 'yes']
    
    print("=" * 60)
    print(f"将使用 {method} 方法，因子 {factor}")
    
    confirm = input("确定开始调整吗？(y/N): ")
    if confirm.lower() in ['y', 'yes']:
        process_all_nifti_files(directory, factor, method, create_plots)

def quick_contrast_adjust():
    """快速对比度调整"""
    directory = "/media/dell/T7 Shield/nnunet/AllData/ZJYY/15(all)plus93(livertumor)_pre/ZJYY_15/dicom_to_nii_15"
    
    # 推荐参数
    contrast_factor = 2.0  # 中等对比度增强
    method = 'linear'          # 线性调整
    create_plots = False       # 不创建对比图
    
    print("快速对比度调整...")
    process_all_nifti_files(directory, contrast_factor, method, create_plots)

# 不同对比度调整的预设
PRESETS = {
    'mild': {'factor': 1.3, 'method': 'linear'},
    'medium': {'factor': 1.8, 'method': 'linear'},
    'strong': {'factor': 2.5, 'method': 'linear'},
    'gamma_light': {'factor': 1.5, 'method': 'gamma'},
    'gamma_dark': {'factor': 0.7, 'method': 'gamma'},
    'histogram': {'factor': 1.0, 'method': 'histogram'}
}

def apply_preset(preset_name):
    """应用预设的对比度调整"""
    if preset_name not in PRESETS:
        print(f"未知预设: {preset_name}")
        print(f"可用预设: {list(PRESETS.keys())}")
        return
    
    preset = PRESETS[preset_name]
    directory = "/media/dell/T7 Shield/nnunet/AllData/ZJYY/dicom_to_nii"
    
    print(f"应用预设: {preset_name}")
    print(f"方法: {preset['method']}, 因子: {preset['factor']}")
    
    process_all_nifti_files(directory, preset['factor'], preset['method'], False)

if __name__ == "__main__":
    # 方法1: 快速调整（推荐）
    quick_contrast_adjust()
    
    # 方法2: 交互式调整（取消注释使用）
    # interactive_adjustment()
    
    # 方法3: 应用预设（取消注释使用）
    # apply_preset('medium')  # 尝试 'mild', 'medium', 'strong', 'gamma_light', 'histogram'
    
    # 方法4: 批量调整（取消注释使用）
    # batch_contrast_adjustment()