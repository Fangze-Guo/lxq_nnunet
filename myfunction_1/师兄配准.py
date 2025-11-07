import SimpleITK as sitk
import numpy as np
from glob import glob
from tqdm import tqdm
import os

def register_with_simpleitk(fixed_image_path, moving_image_path, moving_mask_path, output_mask_path):
    """
    使用SimpleITK进行配准
    """
    # 读取图像
    fixed_image = sitk.ReadImage(fixed_image_path, sitk.sitkFloat32)
    moving_image = sitk.ReadImage(moving_image_path, sitk.sitkFloat32)
    moving_mask = sitk.ReadImage(moving_mask_path, sitk.sitkFloat32)
    
    # 初始化配准
    registration_method = sitk.ImageRegistrationMethod()
    
    # 设置相似性度量
    registration_method.SetMetricAsMattesMutualInformation(numberOfHistogramBins=50)
    
    # 设置优化器
    registration_method.SetOptimizerAsGradientDescent(
        learningRate=1.0, 
        numberOfIterations=100,
        convergenceMinimumValue=1e-6,
        convergenceWindowSize=10
    )
    registration_method.SetOptimizerScalesFromPhysicalShift()
    
    # 设置变换
    initial_transform = sitk.CenteredTransformInitializer(
        fixed_image, 
        moving_image, 
        sitk.Euler3DTransform(), 
        sitk.CenteredTransformInitializerFilter.GEOMETRY
    )
    registration_method.SetInitialTransform(initial_transform)
    
    # 设置插值器
    registration_method.SetInterpolator(sitk.sitkLinear)
    
    # 执行配准
    final_transform = registration_method.Execute(fixed_image, moving_image)
    
    # 应用变换到mask
    resampler = sitk.ResampleImageFilter()
    resampler.SetReferenceImage(fixed_image)
    resampler.SetTransform(final_transform)
    resampler.SetInterpolator(sitk.sitkNearestNeighbor)  # mask使用最近邻插值
    registered_mask = resampler.Execute(moving_mask)
    
    # 保存结果
    sitk.WriteImage(registered_mask, output_mask_path)
    
    return registered_mask

# 主程序
precontrast_image_dir = "/media/dell/T7 Shield/nnunet/AllData/HK/finished/precontrast/dicom_to_nii"
hbp_image_dir = "/media/dell/T7 Shield/nnunet/AllData/HK/finished/HBP/same_origent"
precontrast_mask_dir = "/media/dell/T7 Shield/nnunet/AllData/HK/finished/precontrast/mask/GT_livertumor"
output_mask_dir = "/media/dell/T7 Shield/nnunet/AllData/HK/finished/HBP/mask/GT_livertumor_registered"

os.makedirs(output_mask_dir, exist_ok=True)

precontrast_images = sorted(glob(os.path.join(precontrast_image_dir, "*.nii.gz")))

for precontrast_img_path in tqdm(precontrast_images, desc="Processing registration..."):
    filename = os.path.basename(precontrast_img_path)
    
    hbp_img_path = os.path.join(hbp_image_dir, filename)
    precontrast_mask_path = os.path.join(precontrast_mask_dir, filename)
    output_mask_path = os.path.join(output_mask_dir, filename)
    
    if not all(os.path.exists(p) for p in [hbp_img_path, precontrast_mask_path]):
        continue
    
    try:
        registered_mask = register_with_simpleitk(
            hbp_img_path, precontrast_img_path, precontrast_mask_path, output_mask_path
        )
        print(f"Successfully processed: {filename}")
    except Exception as e:
        print(f"Error processing {filename}: {str(e)}")

print("Registration completed!")