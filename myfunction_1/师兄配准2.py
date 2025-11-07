import ants
import numpy as np
from glob import glob
import nibabel as nib
from tqdm import tqdm
import os
import shutil

def check_antspy_version():
    """检查ANTsPy版本并适配API"""
    try:
        # 尝试新版本API
        test_img = ants.read_image
        test_write = ants.write_image
        print("使用ANTsPy新版本API")
        return ants.read_image, ants.write_image
    except:
        try:
            # 尝试旧版本API
            test_img = ants.image_read
            test_write = ants.image_write
            print("使用ANTsPy旧版本API")
            return ants.image_read, ants.image_write
        except:
            print("ANTsPy API检测失败")
            return None, None

def register_liver_tumor_antspy(fixed_image_path, moving_image_path, moving_mask_path, output_mask_path, registration_type='SyN'):
    """
    使用ANTsPy进行肝脏肿瘤配准
    
    参数:
    fixed_image_path: 目标期相图像路径 (HBP)
    moving_image_path: 源期相图像路径 (precontrast)  
    moving_mask_path: 源期相mask路径
    output_mask_path: 输出配准后的mask路径
    registration_type: 配准类型
    """
    
    # 获取正确的API函数
    read_image, write_image = check_antspy_version()
    if read_image is None:
        raise ImportError("ANTsPy API不可用")
    
    # 读取图像
    fixed_image = read_image(fixed_image_path)
    moving_image = read_image(moving_image_path)
    moving_mask = read_image(moving_mask_path)
    
    print(f"Processing: {os.path.basename(fixed_image_path)}")
    print(f"Fixed image shape: {fixed_image.shape}, spacing: {fixed_image.spacing}")
    print(f"Moving image shape: {moving_image.shape}, spacing: {moving_image.spacing}")
    print(f"Moving mask shape: {moving_mask.shape}")
    
    # 预处理：确保图像数据类型一致
    fixed_image = fixed_image.clone('float32')
    moving_image = moving_image.clone('float32')
    moving_mask = moving_mask.clone('float32')
    
    # 根据配准类型选择参数
    if registration_type == 'SyN':
        # 对称归一化 - 适用于非刚性形变
        registration_result = ants.registration(
            fixed=fixed_image,
            moving=moving_image,
            type_of_transform='SyN',
            grad_step=0.2,           # 梯度步长
            flow_sigma=3,            # 流场平滑度
            total_sigma=0,           # 总平滑度
            reg_iterations=[40, 20, 0]  # 多分辨率迭代次数
        )
    elif registration_type == 'SyNCC':
        # 使用互相关度量的SyN - 适用于单模态
        registration_result = ants.registration(
            fixed=fixed_image,
            moving=moving_image,
            type_of_transform='SyNCC',
            grad_step=0.2,
            flow_sigma=3,
            total_sigma=0
        )
    elif registration_type == 'Affine':
        # 仿射配准
        registration_result = ants.registration(
            fixed=fixed_image,
            moving=moving_image,
            type_of_transform='Affine'
        )
    else:
        # 默认使用快速配准
        registration_result = ants.registration(
            fixed=fixed_image,
            moving=moving_image,
            type_of_transform=registration_type
        )
    
    print(f"配准完成，使用的变换: {registration_result['fwdtransforms']}")
    
    # 应用变换到mask - 使用最近邻插值保持二值性
    registered_mask = ants.apply_transforms(
        fixed=fixed_image,
        moving=moving_mask,
        transformlist=registration_result['fwdtransforms'],
        interpolator='nearestNeighbor'
    )
    
    # 可选：对mask进行后处理（形态学操作）
    registered_mask_array = registered_mask.numpy()
    
    # 保存配准后的mask
    write_image(registered_mask, output_mask_path)
    
    # 计算配准质量指标
    try:
        mi_before = ants.image_mutual_information(fixed_image, moving_image)
        # 创建配准后的moving图像用于质量评估
        registered_moving = ants.apply_transforms(
            fixed=fixed_image,
            moving=moving_image,
            transformlist=registration_result['fwdtransforms'],
            interpolator='linear'
        )
        mi_after = ants.image_mutual_information(fixed_image, registered_moving)
        
        print(f"配准质量 - 互信息: 前 {mi_before:.4f}, 后 {mi_after:.4f}, 提升 {((mi_after-mi_before)/mi_before*100):.2f}%")
    except:
        print("配准质量评估跳过")
    
    return registered_mask, registration_result

def batch_register_liver_tumors():
    """批量处理肝脏肿瘤配准"""
    
    # 定义路径
    precontrast_image_dir = "/media/dell/T7 Shield/nnunet/AllData/HK/finished/precontrast/dicom_to_nii"
    hbp_image_dir = "/media/dell/T7 Shield/nnunet/AllData/HK/finished/HBP/same_origent"
    precontrast_mask_dir = "/media/dell/T7 Shield/nnunet/AllData/HK/finished/precontrast/mask/GT_livertumor"
    output_mask_dir = "/media/dell/T7 Shield/nnunet/AllData/HK/finished/HBP/mask/GT_livertumor_registered_2"
    
    # 创建输出目录
    os.makedirs(output_mask_dir, exist_ok=True)
    
    # 获取所有precontrast图像文件
    precontrast_images = sorted(glob(os.path.join(precontrast_image_dir, "*.nii.gz")))
    
    print(f"找到 {len(precontrast_images)} 个precontrast图像")
    
    # 统计信息
    success_count = 0
    fail_count = 0
    
    for precontrast_img_path in tqdm(precontrast_images, desc="肝脏肿瘤配准进度"):
        filename = os.path.basename(precontrast_img_path)
        
        # 构建对应的HBP图像路径和precontrast mask路径
        hbp_img_path = os.path.join(hbp_image_dir, filename)
        precontrast_mask_path = os.path.join(precontrast_mask_dir, filename)
        output_mask_path = os.path.join(output_mask_dir, filename)
        
        # 检查文件是否存在
        if not os.path.exists(hbp_img_path):
            print(f"警告: HBP图像不存在 {hbp_img_path}")
            fail_count += 1
            continue
            
        if not os.path.exists(precontrast_mask_path):
            print(f"警告: Precontrast mask不存在 {precontrast_mask_path}")
            fail_count += 1
            continue
        
        try:
            # 执行配准 - 尝试不同的配准策略
            registered_mask, reg_result = register_liver_tumor_antspy(
                fixed_image_path=hbp_img_path,          # HBP期相作为目标
                moving_image_path=precontrast_img_path, # precontrast期相作为源
                moving_mask_path=precontrast_mask_path, # precontrast期的mask
                output_mask_path=output_mask_path,
                registration_type='SyN'  # 使用对称归一化配准
            )
            
            success_count += 1
            print(f"✓ 成功处理: {filename}")
            
        except Exception as e:
            print(f"✗ 处理失败 {filename}: {str(e)}")
            fail_count += 1
            continue
    
    print(f"\n配准完成统计:")
    print(f"成功: {success_count}")
    print(f"失败: {fail_count}")
    print(f"成功率: {(success_count/(success_count+fail_count))*100:.2f}%")

def visualize_registration_results(sample_file):
    """可视化配准结果（可选）"""
    import matplotlib.pyplot as plt
    
    # 获取正确的API函数
    read_image, write_image = check_antspy_version()
    
    # 构建路径
    precontrast_path = os.path.join("/media/dell/T7 Shield/nnunet/AllData/HK/finished/precontrast/dicom_to_nii", sample_file)
    hbp_path = os.path.join("/media/dell/T7 Shield/nnunet/AllData/HK/finished/HBP/same_origent", sample_file)
    precontrast_mask_path = os.path.join("/media/dell/T7 Shield/nnunet/AllData/HK/finished/precontrast/mask/GT_livertumor", sample_file)
    registered_mask_path = os.path.join("/media/dell/T7 Shield/nnunet/AllData/HK/finished/HBP/mask/GT_livertumor_registered_2", sample_file)
    
    if all(os.path.exists(p) for p in [precontrast_path, hbp_path, precontrast_mask_path, registered_mask_path]):
        # 读取图像
        precontrast = read_image(precontrast_path)
        hbp = read_image(hbp_path)
        original_mask = read_image(precontrast_mask_path)
        registered_mask = read_image(registered_mask_path)
        
        # 可视化
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        
        # 中间切片
        slice_idx = precontrast.shape[2] // 2
        
        # 显示原始图像和mask
        axes[0,0].imshow(precontrast.numpy()[:,:,slice_idx], cmap='gray')
        axes[0,0].set_title('Precontrast Image')
        
        axes[0,1].imshow(original_mask.numpy()[:,:,slice_idx], cmap='jet', alpha=0.5)
        axes[0,1].set_title('Original Mask')
        
        axes[0,2].imshow(precontrast.numpy()[:,:,slice_idx], cmap='gray')
        axes[0,2].imshow(original_mask.numpy()[:,:,slice_idx], cmap='jet', alpha=0.5)
        axes[0,2].set_title('Precontrast + Mask')
        
        # 显示配准后的结果
        axes[1,0].imshow(hbp.numpy()[:,:,slice_idx], cmap='gray')
        axes[1,0].set_title('HBP Image')
        
        axes[1,1].imshow(registered_mask.numpy()[:,:,slice_idx], cmap='jet', alpha=0.5)
        axes[1,1].set_title('Registered Mask')
        
        axes[1,2].imshow(hbp.numpy()[:,:,slice_idx], cmap='gray')
        axes[1,2].imshow(registered_mask.numpy()[:,:,slice_idx], cmap='jet', alpha=0.5)
        axes[1,2].set_title('HBP + Registered Mask')
        
        plt.tight_layout()
        plt.savefig('/media/dell/T7 Shield/nnunet/AllData/HK/finished/registration_visualization.png', dpi=150, bbox_inches='tight')
        plt.show()

if __name__ == "__main__":
    # 执行批量配准
    batch_register_liver_tumors()
    
    # 可选：可视化一个样本的结果
    # visualize_registration_results("AD5737817.nii.gz")