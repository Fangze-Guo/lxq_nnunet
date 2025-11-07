#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
稳健的医学图像配准脚本：
支持刚性 + B-spline 级联，带重叠检测与回退策略。
"""

import os
import SimpleITK as sitk
import numpy as np
from pathlib import Path

# ===============================
# 用户配置部分
# ===============================
moving_dir = "/media/dell/T7 Shield/nnunet/AllData/HK/dicom_to_nii_gandan"
fixed_dir = "/media/dell/T7 Shield/nnunet/AllData/HK/dicom_to_nii_precontrast"
output_dir = "/media/dell/T7 Shield/nnunet/AllData/HK/dicom_to_nii_gandan_registered_robust"
os.makedirs(output_dir, exist_ok=True)

# 参数（可调）
BSPLINE_MESH = [6, 6, 6]
RIGID_ITERS = 200
BSPLINE_ITERS = 200
RIGID_LR = 1.0
BSPLINE_LR = 0.5
OVERLAP_THRESHOLD = 0.01
DEFAULT_PIXEL_VALUE = 0.0

# ===============================
# 辅助函数
# ===============================

def image_stats(img):
    arr = sitk.GetArrayViewFromImage(img)
    return float(arr.min()), float(arr.max()), float(arr.mean()), float(arr.std()), int(np.count_nonzero(arr))

def save_nifti(img, path):
    sitk.WriteImage(img, path)
    print("  ✅ Saved:", path)

def compute_overlap_fraction(fixed_img, moved_img):
    fa = sitk.GetArrayViewFromImage(fixed_img)
    ma = sitk.GetArrayViewFromImage(moved_img)
    fixed_nonzero = (fa != 0)
    moved_nonzero = (ma != 0)
    if fixed_nonzero.sum() == 0:
        return 0.0
    intersection = np.logical_and(fixed_nonzero, moved_nonzero).sum()
    return float(intersection) / float(fixed_nonzero.sum())

# ===============================
# 主流程
# ===============================

moving_files = sorted([f for f in os.listdir(moving_dir) if f.endswith(".nii") or f.endswith(".nii.gz")])

for filename in moving_files:
    print("\n======================================")
    print("🧩 处理文件:", filename)
    print("======================================")

    moving_path = os.path.join(moving_dir, filename)
    fixed_path = os.path.join(fixed_dir, filename)

    if not os.path.exists(fixed_path):
        print(f"❌ 找不到匹配的参考图像: {fixed_path}")
        continue

    fixed_image = sitk.ReadImage(fixed_path, sitk.sitkFloat32)
    moving_image = sitk.ReadImage(moving_path, sitk.sitkFloat32)

    name = Path(filename).stem.replace(".nii", "")
    out_rigid_path = os.path.join(output_dir, f"{name}_rigid.nii.gz")
    out_final_path = os.path.join(output_dir, f"{name}_registered.nii.gz")

    print(f" Fixed size: {fixed_image.GetSize()}, spacing: {fixed_image.GetSpacing()}")
    print(f" Moving size: {moving_image.GetSize()}, spacing: {moving_image.GetSpacing()}")

    # -----------------------------------
    # Step 1: 刚性配准
    # -----------------------------------
    print("\n🚀 Step 1: 刚性配准 (MOMENTS 初始化)")
    rigid_method = sitk.ImageRegistrationMethod()
    rigid_method.SetMetricAsMattesMutualInformation(numberOfHistogramBins=50)
    rigid_method.SetOptimizerAsGradientDescent(
        learningRate=RIGID_LR,
        numberOfIterations=RIGID_ITERS,
        convergenceMinimumValue=1e-6,
        convergenceWindowSize=10
    )
    rigid_method.SetOptimizerScalesFromPhysicalShift()
    rigid_method.SetInterpolator(sitk.sitkLinear)
    rigid_method.SetShrinkFactorsPerLevel([4, 2, 1])
    rigid_method.SetSmoothingSigmasPerLevel([2, 1, 0])
    rigid_method.SmoothingSigmasAreSpecifiedInPhysicalUnitsOn()

    # 初始化刚性
    initial_rigid = sitk.CenteredTransformInitializer(
        fixed_image, moving_image, sitk.Euler3DTransform(),
        sitk.CenteredTransformInitializerFilter.MOMENTS
    )
    rigid_method.SetInitialTransform(initial_rigid, inPlace=False)

    try:
        rigid_transform = rigid_method.Execute(fixed_image, moving_image)
    except Exception as e:
        print("  ⚠️ 刚性配准失败:", e)
        print("  尝试使用 GEOMETRY 初始化...")
        initial_rigid = sitk.CenteredTransformInitializer(
            fixed_image, moving_image, sitk.Euler3DTransform(),
            sitk.CenteredTransformInitializerFilter.GEOMETRY
        )
        rigid_method.SetInitialTransform(initial_rigid, inPlace=False)
        rigid_transform = rigid_method.Execute(fixed_image, moving_image)

    moved_rigid = sitk.Resample(
        moving_image, fixed_image, rigid_transform,
        sitk.sitkLinear, DEFAULT_PIXEL_VALUE, moving_image.GetPixelID()
    )
    save_nifti(moved_rigid, out_rigid_path)

    overlap = compute_overlap_fraction(fixed_image, moved_rigid)
    print(f"  刚性重采样 overlap: {overlap:.6f}")

    # 回退策略
    if overlap < OVERLAP_THRESHOLD:
        print(f"  ⚠️ overlap={overlap:.6f} < {OVERLAP_THRESHOLD}, 尝试 CopyInformation 回退...")
        moving_copyinfo = sitk.Image(moving_image)
        moving_copyinfo.CopyInformation(fixed_image)
        moved_copyinfo = sitk.Resample(
            moving_copyinfo, fixed_image, sitk.Euler3DTransform(),
            sitk.sitkLinear, DEFAULT_PIXEL_VALUE, moving_copyinfo.GetPixelID()
        )
        temp_overlap = compute_overlap_fraction(fixed_image, moved_copyinfo)
        if temp_overlap > overlap:
            print(f"  ✅ CopyInformation 改进 overlap={temp_overlap:.6f}")
            moved_rigid = moved_copyinfo
            rigid_transform = sitk.Euler3DTransform()

    # -----------------------------------
    # # Step 2: B-spline 非刚性配准
    # # -----------------------------------
    # print("\n🧠 Step 2: B-spline 非刚性配准")
    # registration_method = sitk.ImageRegistrationMethod()
    # registration_method.SetMetricAsMattesMutualInformation(numberOfHistogramBins=50)
    # registration_method.SetOptimizerAsGradientDescent(
    #     learningRate=BSPLINE_LR,
    #     numberOfIterations=BSPLINE_ITERS,
    #     convergenceMinimumValue=1e-6,
    #     convergenceWindowSize=20
    # )
    # registration_method.SetOptimizerScalesFromPhysicalShift()
    # registration_method.SetInterpolator(sitk.sitkLinear)
    # registration_method.SetShrinkFactorsPerLevel([4, 2, 1])
    # registration_method.SetSmoothingSigmasPerLevel([2, 1, 0])
    # registration_method.SmoothingSigmasAreSpecifiedInPhysicalUnitsOn()

    # bspline_init = sitk.BSplineTransformInitializer(fixed_image, BSPLINE_MESH)
    # registration_method.SetInitialTransformAsBSpline(bspline_init, inPlace=False, scaleFactors=[1, 2, 4])
    # registration_method.SetMovingInitialTransform(rigid_transform)

    # try:
    #     bspline_transform = registration_method.Execute(fixed_image, moving_image)
    #     print("  ✅ B-spline 配准完成")
    # except Exception as e:
    #     print("  ❌ B-spline 配准失败:", e)
    #     print("  尝试使用更保守参数重试...")
    #     registration_method.SetOptimizerAsGradientDescent(
    #         learningRate=BSPLINE_LR * 0.5,
    #         numberOfIterations=BSPLINE_ITERS * 2
    #     )
    #     bspline_transform = registration_method.Execute(fixed_image, moving_image)

    # # 合并刚性与非刚性变换
    # composite = sitk.CompositeTransform(3)
    # composite.AddTransform(rigid_transform)
    # composite.AddTransform(bspline_transform)

    # # 最终重采样
    # registered_image = sitk.Resample(
    #     moving_image, fixed_image, composite,
    #     sitk.sitkLinear, DEFAULT_PIXEL_VALUE, moving_image.GetPixelID()
    # )
    # save_nifti(registered_image, out_final_path)

    # mn, mx, mean, std, nz = image_stats(registered_image)
    # print(f" Final stats: min={mn:.3f}, max={mx:.3f}, mean={mean:.3f}, std={std:.3f}, nonzero={nz}")

print("\n🎯 全部任务完成。")
