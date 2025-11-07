#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量坐标系统转换脚本
将HBP目录中的所有图像转换到与precontrast目录相同的坐标系统
"""

import os
import numpy as np
import nibabel as nib
import SimpleITK as sitk
from pathlib import Path
import argparse

def get_matching_files(hbp_dir, precontrast_dir):
    """获取匹配的文件列表"""
    hbp_files = sorted([f for f in os.listdir(hbp_dir) if f.endswith(".nii.gz")])
    precontrast_files = sorted([f for f in os.listdir(precontrast_dir) if f.endswith(".nii.gz")])
    
    common_filenames = set(hbp_files) & set(precontrast_files)
    
    if not common_filenames:
        print("❌ 未找到两个目录中共同的文件")
        return []
    
    result_files = []
    for filename in sorted(common_filenames):
        file_info = {
            'filename': filename,
            'hbp_path': os.path.join(hbp_dir, filename),
            'precontrast_path': os.path.join(precontrast_dir, filename)
        }
        result_files.append(file_info)
    
    return result_files

def analyze_target_coordinate_system(target_path):
    """分析目标坐标系统"""
    target_img = nib.load(target_path)
    
    print(f"🎯 目标坐标系统分析 ({Path(target_path).name}):")
    print(f"  图像尺寸: {target_img.shape}")
    print(f"  体素尺寸: {target_img.header.get_zooms()}")
    print(f"  坐标方向: {nib.aff2axcodes(target_img.affine)}")
    print(f"  原点位置: {target_img.affine[:3, 3]}")
    
    return target_img

def transform_to_target_coordinate_system(source_path, target_path, output_path):
    """
    将源图像转换到目标图像的坐标系统
    """
    print(f"\n🔄 处理: {Path(source_path).name}")
    
    # 加载图像
    source_sitk = sitk.ReadImage(source_path)
    target_sitk = sitk.ReadImage(target_path)
    
    print(f"  📊 源图像信息:")
    print(f"    尺寸: {source_sitk.GetSize()}, 间距: {source_sitk.GetSpacing()}")
    print(f"    原点: {source_sitk.GetOrigin()}, 方向: {source_sitk.GetDirection()}")
    
    print(f"  🎯 目标图像信息:")
    print(f"    尺寸: {target_sitk.GetSize()}, 间距: {target_sitk.GetSpacing()}")
    print(f"    原点: {target_sitk.GetOrigin()}, 方向: {target_sitk.GetDirection()}")
    
    # 使用SimpleITK进行精确的物理空间重采样
    resampler = sitk.ResampleImageFilter()
    resampler.SetReferenceImage(target_sitk)  # 使用目标图像作为参考
    
    # 设置重采样参数
    resampler.SetInterpolator(sitk.sitkLinear)
    resampler.SetDefaultPixelValue(0.0)
    
    # 执行重采样
    resampled_sitk = resampler.Execute(source_sitk)
    
    print(f"  ✅ 重采样完成:")
    print(f"    新尺寸: {resampled_sitk.GetSize()}, 新间距: {resampled_sitk.GetSpacing()}")
    print(f"    新原点: {resampled_sitk.GetOrigin()}, 新方向: {resampled_sitk.GetDirection()}")
    
    # 保存结果
    sitk.WriteImage(resampled_sitk, output_path)
    print(f"  💾 保存到: {output_path}")
    
    # 验证转换结果
    verify_coordinate_alignment(output_path, target_path)
    
    return resampled_sitk

def verify_coordinate_alignment(transformed_path, target_path):
    """验证坐标系统对齐"""
    transformed_img = nib.load(transformed_path)
    target_img = nib.load(target_path)
    
    print(f"  🔍 坐标对齐验证:")
    print(f"    尺寸一致: {transformed_img.shape == target_img.shape}")
    print(f"    体素尺寸一致: {np.allclose(transformed_img.header.get_zooms(), target_img.header.get_zooms(), atol=1e-3)}")
    print(f"    仿射矩阵一致: {np.allclose(transformed_img.affine, target_img.affine, atol=1e-3)}")
    print(f"    方向一致: {nib.aff2axcodes(transformed_img.affine) == nib.aff2axcodes(target_img.affine)}")

def batch_transform_coordinate_systems(hbp_dir, precontrast_dir, output_dir):
    """批量转换坐标系统"""
    print("=" * 80)
    print("🔄 批量坐标系统转换")
    print("=" * 80)
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 获取匹配的文件
    file_list = get_matching_files(hbp_dir, precontrast_dir)
    
    if not file_list:
        print("❌ 没有找到匹配的文件")
        return
    
    print(f"📊 找到 {len(file_list)} 对匹配的文件")
    
    success_count = 0
    
    for file_info in file_list:
        filename = file_info['filename']
        hbp_path = file_info['hbp_path']
        precontrast_path = file_info['precontrast_path']
        output_path = os.path.join(output_dir, filename)
        
        print(f"\n{'='*60}")
        print(f"🧩 处理文件: {filename}")
        print(f"{'='*60}")
        
        try:
            # 转换坐标系统
            transform_to_target_coordinate_system(hbp_path, precontrast_path, output_path)
            success_count += 1
            print(f"  ✅ 转换成功: {filename}")
            
        except Exception as e:
            print(f"❌ 转换失败: {filename}")
            print(f"   错误: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    # 最终统计
    print("\n" + "=" * 80)
    print("📈 转换完成统计")
    print("=" * 80)
    print(f"总文件数: {len(file_list)}")
    print(f"成功转换: {success_count}")
    print(f"失败: {len(file_list) - success_count}")
    print(f"输出目录: {output_dir}")
    print("=" * 80)

def create_comparison_report(hbp_dir, precontrast_dir, output_dir):
    """创建转换前后的对比报告"""
    print("\n" + "=" * 80)
    print("📋 坐标系统转换对比报告")
    print("=" * 80)
    
    file_list = get_matching_files(hbp_dir, precontrast_dir)
    
    for file_info in file_list:
        filename = file_info['filename']
        hbp_path = file_info['hbp_path']
        precontrast_path = file_info['precontrast_path']
        output_path = os.path.join(output_dir, filename)
        
        if not os.path.exists(output_path):
            continue
            
        print(f"\n📄 文件: {filename}")
        print("-" * 40)
        
        # 加载三个图像进行比较
        original_hbp = nib.load(hbp_path)
        target_precontrast = nib.load(precontrast_path)
        transformed_hbp = nib.load(output_path)
        
        print("原始HBP图像:")
        print(f"  尺寸: {original_hbp.shape}, 体素: {original_hbp.header.get_zooms()}")
        print(f"  方向: {nib.aff2axcodes(original_hbp.affine)}")
        
        print("目标Precontrast图像:")
        print(f"  尺寸: {target_precontrast.shape}, 体素: {target_precontrast.header.get_zooms()}")
        print(f"  方向: {nib.aff2axcodes(target_precontrast.affine)}")
        
        print("转换后HBP图像:")
        print(f"  尺寸: {transformed_hbp.shape}, 体素: {transformed_hbp.header.get_zooms()}")
        print(f"  方向: {nib.aff2axcodes(transformed_hbp.affine)}")
        
        # 检查对齐情况
        size_match = transformed_hbp.shape == target_precontrast.shape
        voxel_match = np.allclose(transformed_hbp.header.get_zooms(), target_precontrast.header.get_zooms(), atol=1e-3)
        affine_match = np.allclose(transformed_hbp.affine, target_precontrast.affine, atol=1e-3)
        
        print(f"✅ 对齐状态: 尺寸={size_match}, 体素={voxel_match}, 仿射={affine_match}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="批量坐标系统转换工具")
    parser.add_argument("--hbp_dir", type=str, required=True, 
                       help="HBP图像目录路径")
    parser.add_argument("--precontrast_dir", type=str, required=True,
                       help="Precontrast图像目录路径")
    parser.add_argument("--output_dir", type=str, required=True,
                       help="输出目录路径")
    parser.add_argument("--create_report", action="store_true",
                       help="创建转换对比报告")
    args = parser.parse_args()
    # 执行批量转换
    batch_transform_coordinate_systems(args.hbp_dir, args.precontrast_dir, args.output_dir)
    
    # 如果需要，创建对比报告
    if args.create_report:
        create_comparison_report(args.hbp_dir, args.precontrast_dir, args.output_dir)