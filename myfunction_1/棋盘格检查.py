#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Diagnostic script for black warped image issue
"""

import os
import numpy as np
import nibabel as nib
import matplotlib.pyplot as plt

def analyze_image_properties(img_path, name):
    """详细分析图像属性"""
    print(f"\n📊 Analyzing {name}: {os.path.basename(img_path)}")
    print("-" * 50)
    
    img = nib.load(img_path)
    data = img.get_fdata()
    
    # 基本统计
    print(f"Shape: {data.shape}")
    print(f"Data type: {data.dtype}")
    print(f"Min value: {data.min():.6f}")
    print(f"Max value: {data.max():.6f}")
    print(f"Mean value: {data.mean():.6f}")
    print(f"Std value: {data.std():.6f}")
    
    # 检查零值比例
    zero_ratio = np.sum(data == 0) / data.size * 100
    print(f"Zero values: {zero_ratio:.2f}%")
    
    # 检查负值
    negative_ratio = np.sum(data < 0) / data.size * 100
    print(f"Negative values: {negative_ratio:.2f}%")
    
    # 检查有效数据范围
    nonzero_data = data[data != 0]
    if len(nonzero_data) > 0:
        print(f"Non-zero min: {nonzero_data.min():.6f}")
        print(f"Non-zero max: {nonzero_data.max():.6f}")
        print(f"Non-zero mean: {nonzero_data.mean():.6f}")
    
    # 强度分布百分位数
    percentiles = [1, 5, 10, 25, 50, 75, 90, 95, 99]
    percentile_values = np.percentile(data, percentiles)
    print("Percentiles:")
    for p, v in zip(percentiles, percentile_values):
        print(f"  {p}%: {v:.6f}")
    
    return img, data

def create_comparison_visualization(fixed_data, moving_data, warped_data, slice_idx):
    """创建详细的对比可视化"""
    fig, axes = plt.subplots(3, 4, figsize=(20, 15))
    
    # 第一行：原始强度显示
    vmin_fixed = np.percentile(fixed_data, 1)
    vmax_fixed = np.percentile(fixed_data, 99)
    
    vmin_moving = np.percentile(moving_data, 1)
    vmax_moving = np.percentile(moving_data, 99)
    
    vmin_warped = np.percentile(warped_data, 1)
    vmax_warped = np.percentile(warped_data, 99)
    
    # Fixed image
    im1 = axes[0, 0].imshow(fixed_data[:, :, slice_idx], 
                           cmap='gray', vmin=vmin_fixed, vmax=vmax_fixed)
    axes[0, 0].set_title(f'Fixed\nRange: [{vmin_fixed:.3f}, {vmax_fixed:.3f}]')
    plt.colorbar(im1, ax=axes[0, 0])
    
    # Moving image
    im2 = axes[0, 1].imshow(moving_data[:, :, slice_idx], 
                           cmap='gray', vmin=vmin_moving, vmax=vmax_moving)
    axes[0, 1].set_title(f'Moving\nRange: [{vmin_moving:.3f}, {vmax_moving:.3f}]')
    plt.colorbar(im2, ax=axes[0, 1])
    
    # Warped image - 原始范围
    im3 = axes[0, 2].imshow(warped_data[:, :, slice_idx], 
                           cmap='gray', vmin=vmin_warped, vmax=vmax_warped)
    axes[0, 2].set_title(f'Warped - Original\nRange: [{vmin_warped:.3f}, {vmax_warped:.3f}]')
    plt.colorbar(im3, ax=axes[0, 2])
    
    # Warped image - 强制使用Fixed的范围
    im4 = axes[0, 3].imshow(warped_data[:, :, slice_idx], 
                           cmap='gray', vmin=vmin_fixed, vmax=vmax_fixed)
    axes[0, 3].set_title(f'Warped - Fixed Range\nRange: [{vmin_fixed:.3f}, {vmax_fixed:.3f}]')
    plt.colorbar(im4, ax=axes[0, 3])
    
    # 第二行：归一化显示
    def normalize_to_range(data, target_min, target_max):
        data_min = np.percentile(data, 1)
        data_max = np.percentile(data, 99)
        normalized = (data - data_min) / (data_max - data_min + 1e-8)
        return normalized * (target_max - target_min) + target_min
    
    # 各自归一化
    fixed_norm = normalize_to_range(fixed_data[:, :, slice_idx], 0, 1)
    moving_norm = normalize_to_range(moving_data[:, :, slice_idx], 0, 1)
    warped_norm = normalize_to_range(warped_data[:, :, slice_idx], 0, 1)
    
    axes[1, 0].imshow(fixed_norm, cmap='gray', vmin=0, vmax=1)
    axes[1, 0].set_title('Fixed - Normalized')
    
    axes[1, 1].imshow(moving_norm, cmap='gray', vmin=0, vmax=1)
    axes[1, 1].set_title('Moving - Normalized')
    
    axes[1, 2].imshow(warped_norm, cmap='gray', vmin=0, vmax=1)
    axes[1, 2].set_title('Warped - Normalized')
    
    # 直方图
    axes[1, 3].hist(fixed_data.flatten(), bins=100, alpha=0.7, label='Fixed', density=True)
    axes[1, 3].hist(moving_data.flatten(), bins=100, alpha=0.7, label='Moving', density=True)
    axes[1, 3].hist(warped_data.flatten(), bins=100, alpha=0.7, label='Warped', density=True)
    axes[1, 3].set_title('Intensity Histograms')
    axes[1, 3].legend()
    axes[1, 3].set_yscale('log')
    
    # 第三行：差异分析
    diff_before = np.abs(fixed_data[:, :, slice_idx] - moving_data[:, :, slice_idx])
    diff_after = np.abs(fixed_data[:, :, slice_idx] - warped_data[:, :, slice_idx])
    
    axes[2, 0].imshow(diff_before, cmap='hot')
    axes[2, 0].set_title(f'Diff: Fixed vs Moving\nMean: {diff_before.mean():.3f}')
    plt.colorbar(axes[2, 0].imshow(diff_before, cmap='hot'), ax=axes[2, 0])
    
    axes[2, 1].imshow(diff_after, cmap='hot')
    axes[2, 1].set_title(f'Diff: Fixed vs Warped\nMean: {diff_after.mean():.3f}')
    plt.colorbar(axes[2, 1].imshow(diff_after, cmap='hot'), ax=axes[2, 1])
    
    # 改进的棋盘格
    def enhanced_checkerboard(fixed, moving, block_size=16):
        checker_mask = np.zeros(fixed.shape, dtype=bool)
        for i in range(0, fixed.shape[0], block_size):
            for j in range(0, fixed.shape[1], block_size):
                if ((i // block_size) + (j // block_size)) % 2 == 0:
                    checker_mask[i:i+block_size, j:j+block_size] = True
        
        # 使用归一化后的数据
        fixed_norm = normalize_to_range(fixed, 0, 1)
        moving_norm = normalize_to_range(moving, 0, 1)
        checkerboard = np.where(checker_mask, fixed_norm, moving_norm)
        return checkerboard
    
    checker_before = enhanced_checkerboard(fixed_data[:, :, slice_idx], moving_data[:, :, slice_idx])
    checker_after = enhanced_checkerboard(fixed_data[:, :, slice_idx], warped_data[:, :, slice_idx])
    
    axes[2, 2].imshow(checker_before, cmap='gray')
    axes[2, 2].set_title('Checkerboard - Before')
    
    axes[2, 3].imshow(checker_after, cmap='gray')
    axes[2, 3].set_title('Checkerboard - After')
    
    plt.tight_layout()
    plt.show()
    
    return diff_before.mean(), diff_after.mean()

def main():
    """主诊断函数"""
    # 文件路径
    fixed_path = "/media/dell/T7 Shield/nnunet/AllData/HK/finished/HBP/same_origent/AF0094212.nii.gz"
    moving_path = "/media/dell/T7 Shield/nnunet/AllData/HK/finished/precontrast/dicom_to_nii/AF0094212.nii.gz"
    warped_path = "/media/dell/T7 Shield/nnunet/AllData/HK/finished/precontrast/mask/peizhun/livertumor/AF0094212.nii_warped_moving.nii.gz"
    
    print("🔍 Diagnostic Analysis for Black Warped Image Issue")
    print("=" * 60)
    
    # 分析所有图像
    fixed_img, fixed_data = analyze_image_properties(fixed_path, "Fixed Image")
    moving_img, moving_data = analyze_image_properties(moving_path, "Moving Image")
    warped_img, warped_data = analyze_image_properties(warped_path, "Warped Image")
    
    # 选择中心切片
    slice_idx = fixed_data.shape[2] // 2
    print(f"\n📊 Using center slice: {slice_idx}")
    
    # 创建详细的可视化
    mean_diff_before, mean_diff_after = create_comparison_visualization(
        fixed_data, moving_data, warped_data, slice_idx
    )
    
    # 诊断结论
    print(f"\n🎯 DIAGNOSTIC CONCLUSIONS:")
    print("=" * 40)
    
    warped_range = warped_data.max() - warped_data.min()
    fixed_range = fixed_data.max() - fixed_data.min()
    
    print(f"1. Warped image data range: {warped_range:.6f}")
    print(f"2. Fixed image data range: {fixed_range:.6f}")
    print(f"3. Range ratio (warped/fixed): {warped_range/fixed_range:.6f}")
    print(f"4. Mean difference before registration: {mean_diff_before:.6f}")
    print(f"5. Mean difference after registration: {mean_diff_after:.6f}")
    
    if warped_range < 0.001:
        print("❌ PROBLEM: Warped image has very small data range (likely all zeros or near-zero)")
    elif mean_diff_after > mean_diff_before:
        print("❌ PROBLEM: Registration increased the difference (registration failed)")
    else:
        print("✅ Warped image has reasonable data range")
    
    print(f"\n💡 SUGGESTIONS:")
    if warped_range < 0.001:
        print("  - Check the registration process parameters")
        print("  - Verify that the warped image was saved correctly")
        print("  - Check if intensity normalization was too aggressive")
        print("  - Try re-running the registration with different settings")

if __name__ == "__main__":
    main()