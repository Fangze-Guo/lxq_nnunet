#!/usr/bin/env python3
import nibabel as nib
import numpy as np
import os

def analyze_coordinate_system(file1, file2):
    """
    分析两个NIfTI文件的坐标系统是否一致
    """
    print("=" * 80)
    print("🔍 坐标系统一致性分析")
    print("=" * 80)
    
    # 加载两个文件
    img1 = nib.load(file1)
    img2 = nib.load(file2)
    
    # 获取基本信息
    print(f"文件1: {file1}")
    print(f"文件2: {file2}")
    print()
    
    # 1. 检查图像尺寸
    print("📏 图像尺寸:")
    print(f"  文件1: {img1.shape}")
    print(f"  文件2: {img2.shape}")
    print(f"  尺寸一致: {img1.shape == img2.shape}")
    print()
    
    # 2. 检查体素尺寸
    print("📐 体素尺寸 (mm):")
    zooms1 = img1.header.get_zooms()
    zooms2 = img2.header.get_zooms()
    print(f"  文件1: {zooms1}")
    print(f"  文件2: {zooms2}")
    print(f"  体素尺寸一致: {np.allclose(zooms1, zooms2, atol=1e-3)}")
    print()
    
    # 3. 检查仿射矩阵
    print("🧮 仿射矩阵:")
    print(f"  文件1:\n{img1.affine}")
    print(f"  文件2:\n{img2.affine}")
    print(f"  仿射矩阵一致: {np.allclose(img1.affine, img2.affine, atol=1e-3)}")
    print()
    
    # 4. 检查坐标系统
    print("🎯 坐标系统信息:")
    
    # 获取方向代码
    orient1 = nib.aff2axcodes(img1.affine)
    orient2 = nib.aff2axcodes(img2.affine)
    print(f"  文件1方向: {orient1}")
    print(f"  文件2方向: {orient2}")
    print(f"  方向一致: {orient1 == orient2}")
    print()
    
    # 5. 检查sform和qform
    print("📋 sform和qform信息:")
    
    sform1 = img1.get_sform()
    sform2 = img2.get_sform()
    qform1 = img1.get_qform()
    qform2 = img2.get_qform()
    
    sform_code1 = img1.header['sform_code']
    sform_code2 = img2.header['sform_code']
    qform_code1 = img1.header['qform_code']
    qform_code2 = img2.header['qform_code']
    
    print(f"  文件1 - sform_code: {sform_code1}, qform_code: {qform_code1}")
    print(f"  文件2 - sform_code: {sform_code2}, qform_code: {qform_code2}")
    print(f"  sform一致: {np.allclose(sform1, sform2, atol=1e-3)}")
    print(f"  qform一致: {np.allclose(qform1, qform2, atol=1e-3)}")
    print()
    
    # 6. 检查数据范围
    print("📊 数据统计:")
    data1 = img1.get_fdata()
    data2 = img2.get_fdata()
    
    print(f"  文件1 - 范围: [{data1.min():.3f}, {data1.max():.3f}], 均值: {data1.mean():.3f}")
    print(f"  文件2 - 范围: [{data2.min():.3f}, {data2.max():.3f}], 均值: {data2.mean():.3f}")
    print()
    
    # 7. 检查原点位置
    print("📍 原点位置 (世界坐标):")
    origin1 = img1.affine[:3, 3]
    origin2 = img2.affine[:3, 3]
    print(f"  文件1原点: {origin1}")
    print(f"  文件2原点: {origin2}")
    print(f"  原点一致: {np.allclose(origin1, origin2, atol=1e-3)}")
    print()
    
    # 8. 综合评估
    print("📈 综合评估:")
    issues = []
    
    if img1.shape != img2.shape:
        issues.append("❌ 图像尺寸不一致")
    
    if not np.allclose(zooms1, zooms2, atol=1e-3):
        issues.append("❌ 体素尺寸不一致")
    
    if not np.allclose(img1.affine, img2.affine, atol=1e-3):
        issues.append("❌ 仿射矩阵不一致")
    
    if orient1 != orient2:
        issues.append("❌ 坐标方向不一致")
    
    if not np.allclose(origin1, origin2, atol=1e-3):
        issues.append("❌ 原点位置不一致")
    
    if len(issues) == 0:
        print("✅ 两个文件在相同的坐标系统下")
        return True
    else:
        print("⚠️ 检测到以下不一致:")
        for issue in issues:
            print(f"  {issue}")
        return False

def check_orientation_details(file1, file2):
    """
    详细检查方向信息
    """
    print("\n" + "=" * 80)
    print("🧭 详细方向分析")
    print("=" * 80)
    
    img1 = nib.load(file1)
    img2 = nib.load(file2)
    
    # 分析仿射矩阵的方向部分
    def analyze_affine_direction(affine, name):
        print(f"\n{name}的方向分析:")
        # 提取旋转部分 (3x3)
        rotation = affine[:3, :3]
        print(f"  旋转矩阵:\n{rotation}")
        
        # 计算行列式判断是否包含翻转
        det = np.linalg.det(rotation)
        print(f"  行列式: {det:.6f}")
        if det < 0:
            print("  ⚠️ 包含镜像翻转")
        else:
            print("  ✅ 不包含镜像翻转")
        
        # 检查每个轴的方向
        for i, axis in enumerate(['X轴', 'Y轴', 'Z轴']):
            direction = rotation[:, i]
            dominant_idx = np.argmax(np.abs(direction))
            sign = np.sign(direction[dominant_idx])
            
            if dominant_idx == 0:
                direction_str = "右→左" if sign > 0 else "左→右"
            elif dominant_idx == 1:
                direction_str = "前→后" if sign > 0 else "后→前"  
            else:
                direction_str = "上→下" if sign > 0 else "下→上"
                
            print(f"  {axis}: {direction_str} (向量: {direction})")
    
    analyze_affine_direction(img1.affine, "文件1")
    analyze_affine_direction(img2.affine, "文件2")
    
    # 检查是否需要重新定向
    orient1 = nib.aff2axcodes(img1.affine)
    orient2 = nib.aff2axcodes(img2.affine)
    
    print(f"\n🎯 当前方向:")
    print(f"  文件1: {orient1}")
    print(f"  文件2: {orient2}")
    
    if orient1 != orient2:
        print(f"\n🔄 建议重新定向到: RAS")
        print(f"  文件1到RAS: {orient1} → RAS")
        print(f"  文件2到RAS: {orient2} → RAS")

# 要检查的文件路径
file1 = "/media/dell/T7 Shield/nnunet/AllData/HK/finished/HBP/HBP_nii_lps/AD5737817.nii.gz"
file2 = "/media/dell/T7 Shield/nnunet/AllData/HK/finished/precontrast/dicom_to_nii/AD5737817.nii.gz"
# /media/dell/T7 Shield/nnunet/AllData/HK/finished/precontrast/dicom_to_nii
# /media/dell/T7 Shield/nnunet/AllData/HK/finished/HBP/HBP_nii_lps
# 检查文件是否存在
if not os.path.exists(file1):
    print(f"❌ 文件不存在: {file1}")
    exit(1)

if not os.path.exists(file2):
    print(f"❌ 文件不存在: {file2}")
    exit(1)

# 执行分析
try:
    same_coords = analyze_coordinate_system(file1, file2)
    check_orientation_details(file1, file2)
    
    print("\n" + "=" * 80)
    if same_coords:
        print("🎉 结论: 两个文件在相同的坐标系统下，可以直接进行配准")
    else:
        print("💡 结论: 两个文件坐标系统不一致，需要在配准前进行坐标系统对齐")
    print("=" * 80)
    
except Exception as e:
    print(f"❌ 分析过程中出现错误: {e}")
    import traceback
    traceback.print_exc()