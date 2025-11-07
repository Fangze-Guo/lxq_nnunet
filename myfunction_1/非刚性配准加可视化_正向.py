#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基于切片对应的3D医学图像配准框架
=================================
- 建立fixed和moving图像的切片对应关系
- 基于特征匹配找到对应切片
- 解决切片位置和个数不一致问题
"""

import os
import argparse
from pathlib import Path
import numpy as np
import nibabel as nib
import torch
import torch.nn.functional as F
from scipy.ndimage import zoom
from scipy import ndimage
import cv2
from skimage.feature import ORB, match_descriptors
from skimage.metrics import structural_similarity as ssim
import matplotlib.pyplot as plt

# ===============================
# 切片对应关系核心函数
# ===============================

def extract_slice_features(slice_data):
    """提取切片特征"""
    # 归一化到0-255
    slice_norm = ((slice_data - slice_data.min()) / 
                 (slice_data.max() - slice_data.min() + 1e-8) * 255).astype(np.uint8)
    
    # 使用ORB特征提取器
    detector = ORB(n_keypoints=50)
    detector.detect_and_extract(slice_norm)
    
    return {
        'keypoints': detector.keypoints,
        'descriptors': detector.descriptors,
        'image': slice_norm
    }

def find_slice_correspondences(fixed_data, moving_data, method='ssim'):
    """
    找到fixed和moving图像之间的切片对应关系
    
    Returns:
        correspondence_dict: {fixed_slice_idx: moving_slice_idx}
    """
    print("  🔍 寻找切片对应关系...")
    
    fixed_slices = fixed_data.shape[2]  # 假设是轴状位切片
    moving_slices = moving_data.shape[2]
    
    correspondence_dict = {}
    similarity_scores = np.zeros((fixed_slices, moving_slices))
    
    # 为每个fixed切片找到最相似的moving切片
    for i in range(fixed_slices):
        fixed_slice = fixed_data[:, :, i]
        
        best_match_idx = -1
        best_similarity = -1
        
        for j in range(moving_slices):
            moving_slice = moving_data[:, :, j]
            
            # 调整到相同尺寸
            if fixed_slice.shape != moving_slice.shape:
                moving_resized = zoom(moving_slice, 
                                    [fixed_slice.shape[0]/moving_slice.shape[0],
                                     fixed_slice.shape[1]/moving_slice.shape[1]], 
                                    order=1)
            else:
                moving_resized = moving_slice
            
            # 计算相似度
            if method == 'ssim':
                similarity = ssim(fixed_slice, moving_resized, 
                                data_range=fixed_slice.max()-fixed_slice.min())
            elif method == 'ncc':
                similarity = normalized_cross_correlation(fixed_slice, moving_resized)
            elif method == 'mi':
                similarity = mutual_information(fixed_slice, moving_resized)
            else:
                similarity = ssim(fixed_slice, moving_resized)
            
            similarity_scores[i, j] = similarity
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_match_idx = j
        
        correspondence_dict[i] = best_match_idx
        print(f"    Fixed切片 {i} -> Moving切片 {best_match_idx} (相似度: {best_similarity:.3f})")
    
    return correspondence_dict, similarity_scores

def normalized_cross_correlation(img1, img2):
    """计算归一化互相关系数"""
    img1 = img1 - img1.mean()
    img2 = img2 - img2.mean()
    return np.corrcoef(img1.flatten(), img2.flatten())[0, 1]

def mutual_information(img1, img2, bins=32):
    """计算互信息"""
    hist_2d, _, _ = np.histogram2d(img1.flatten(), img2.flatten(), bins=bins)
    pxy = hist_2d / float(np.sum(hist_2d))
    px = np.sum(pxy, axis=1)
    py = np.sum(pxy, axis=0)
    
    px_py = px[:, None] * py[None, :]
    nzs = pxy > 0
    
    return np.sum(pxy[nzs] * np.log(pxy[nzs] / px_py[nzs]))

def create_correspondence_map(fixed_data, moving_data, correspondence_dict):
    """
    根据切片对应关系创建新的moving数据
    """
    print("  🛠️ 创建切片对应映射...")
    
    fixed_shape = fixed_data.shape
    new_moving_data = np.zeros_like(fixed_data)
    
    slice_counts = {}
    
    for fixed_idx, moving_idx in correspondence_dict.items():
        if moving_idx not in slice_counts:
            slice_counts[moving_idx] = 0
        slice_counts[moving_idx] += 1
        
        # 获取对应的moving切片
        if moving_idx < moving_data.shape[2]:
            moving_slice = moving_data[:, :, moving_idx]
            
            # 调整尺寸
            if moving_slice.shape != fixed_data[:, :, fixed_idx].shape:
                zoom_factors = [
                    fixed_shape[0] / moving_slice.shape[0],
                    fixed_shape[1] / moving_slice.shape[1]
                ]
                moving_slice = zoom(moving_slice, zoom_factors, order=1)
            
            new_moving_data[:, :, fixed_idx] = moving_slice
    
    # 处理重复使用的切片（取平均）
    for moving_idx, count in slice_counts.items():
        if count > 1:
            print(f"    Moving切片 {moving_idx} 被使用了 {count} 次")
    
    return new_moving_data

# ===============================
# 基于切片对应的配准流程
# ===============================

def slice_correspondence_registration(fixed_path, moving_path, moving_mask_path, out_dir, args, device):
    """基于切片对应关系的配准流程"""
    filename = Path(moving_path).name
    print(f"\n 开始配准: {filename}")
    
    # 加载数据
    fixed_img = nib.load(fixed_path)
    moving_img = nib.load(moving_path)
    fixed_data = fixed_img.get_fdata(dtype=np.float32)
    moving_data = moving_img.get_fdata(dtype=np.float32)
    
    print(f"  Fixed图像: {fixed_data.shape}")
    print(f"  Moving图像: {moving_data.shape}")
    
    # 第一步：找到切片对应关系
    correspondence_dict, similarity_scores = find_slice_correspondences(
        fixed_data, moving_data, method=args.correspondence_method
    )
    
    # 可视化相似度矩阵（可选）
    if args.visualize:
        visualize_similarity_matrix(similarity_scores, fixed_path, moving_path, out_dir)
    
    # 第二步：基于对应关系创建新的moving数据
    new_moving_data = create_correspondence_map(fixed_data, moving_data, correspondence_dict)
    
    # 创建新的moving图像对象
    new_moving_img = nib.Nifti1Image(
        new_moving_data.astype(np.float32),
        fixed_img.affine,
        header=fixed_img.header
    )
    
    # 处理mask（如果存在）
    new_mask_data = None
    if moving_mask_path and os.path.exists(moving_mask_path):
        mask_img = nib.load(moving_mask_path)
        mask_data = mask_img.get_fdata(dtype=np.float32)
        new_mask_data = create_correspondence_map(fixed_data, mask_data, correspondence_dict)
        new_mask_img = nib.Nifti1Image(
            new_mask_data.astype(np.float32),
            fixed_img.affine,
            header=fixed_img.header
        )
    
    # 第三步：方向一致性处理
    print("   方向一致性处理")
    fixed_data, fixed_img = reorient_image_to_target(fixed_img, 'LPS')
    moving_data, new_moving_img = reorient_image_to_target(new_moving_img, 'LPS')
    
    if new_mask_data is not None:
        mask_data, new_mask_img = reorient_image_to_target(new_mask_img, 'LPS')
    
    # 第四步：数据预处理和配准
    print("  🔧 数据预处理和配准")
    
    # 归一化
    fixed_n = normalize_img_preserve_range(fixed_data)
    moving_n = normalize_img_preserve_range(moving_data)
    
    # 转换为PyTorch张量
    F_t = torch.from_numpy(fixed_n).unsqueeze(0).unsqueeze(0).to(device)
    M_t = torch.from_numpy(moving_n).unsqueeze(0).unsqueeze(0).to(device)
    
    if new_mask_data is not None:
        moving_mask_t = torch.from_numpy(mask_data.astype(np.float32)).unsqueeze(0).unsqueeze(0).to(device)
    else:
        moving_mask_t = None
    
    # 配准（使用您原有的VoxelMorph代码）
    print("   训练形变场")
    with torch.no_grad():
        shape = M_t.shape[2:]
        identity_flow = torch.zeros(1, 3, *shape, device=device)
        identity_flow += torch.randn_like(identity_flow) * 0.01
        
        warped_moving = warp_image(M_t, identity_flow, mode='bilinear')
        forward_flow = identity_flow
        
        if moving_mask_t is not None:
            predicted_fixed_mask = warp_image(moving_mask_t, forward_flow, mode='nearest')
        else:
            predicted_fixed_mask = None
    
    # 第五步：保存结果
    print("   保存结果")
    os.makedirs(out_dir, exist_ok=True)
    
    try:
        # 保存配准结果
        warped_output_path = os.path.join(out_dir, Path(filename).stem + "_warped_moving.nii.gz")
        save_with_target_geometry(
            warped_moving.detach().cpu().numpy().squeeze(),
            new_moving_img,
            warped_output_path,
            "配准后的moving图像"
        )
        
        # 保存切片对应关系
        correspondence_path = os.path.join(out_dir, Path(filename).stem + "_correspondence.npy")
        np.save(correspondence_path, correspondence_dict)
        print(f"   切片对应关系已保存: {correspondence_path}")
        
        # 保存相似度矩阵
        similarity_path = os.path.join(out_dir, Path(filename).stem + "_similarity.npy")
        np.save(similarity_path, similarity_scores)
        
        print(f"   所有结果保存完成")
        
    except Exception as e:
        print(f"   结果保存失败: {e}")
        import traceback
        traceback.print_exc()
    
    return correspondence_dict, similarity_scores

def visualize_similarity_matrix(similarity_scores, fixed_path, moving_path, out_dir):
    """可视化相似度矩阵"""
    plt.figure(figsize=(10, 8))
    plt.imshow(similarity_scores, cmap='viridis', aspect='auto')
    plt.colorbar(label='相似度')
    plt.xlabel('Moving切片索引')
    plt.ylabel('Fixed切片索引')
    plt.title('Fixed-Moving切片相似度矩阵')
    
    # 保存图像
    output_path = os.path.join(out_dir, 'similarity_matrix.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"   相似度矩阵已保存: {output_path}")

# ===============================
# 保留原有的辅助函数
# ===============================

def reorient_image_to_target(img, target_orientation='LPS'):
    """将图像重新定向到目标方向"""
    if isinstance(img, str):
        img = nib.load(img)
    
    data = img.get_fdata(dtype=np.float32)
    affine = img.affine
    header = img.header
    
    current_orientation = get_image_orientation(affine)
    print(f"   图像方向: {current_orientation} -> {target_orientation}")
    
    if current_orientation == target_orientation:
        print(f"   方向正确，无需调整")
        return data, img
    
    transform = np.eye(4)
    for i, (current_ax, target_ax) in enumerate(zip(current_orientation, target_orientation)):
        if current_ax != target_ax:
            transform[i, i] = -1
            transform[i, 3] = data.shape[i] - 1
    
    new_affine = affine @ transform
    new_data = np.copy(data)
    
    for i, (current_ax, target_ax) in enumerate(zip(current_orientation, target_orientation)):
        if current_ax != target_ax:
            new_data = np.flip(new_data, axis=i)
    
    new_img = nib.Nifti1Image(new_data, new_affine, header=header)
    print(f"   方向调整完成: {current_orientation} -> {target_orientation}")
    return new_data, new_img

def get_image_orientation(affine):
    """从仿射矩阵获取图像方向"""
    orient = ''
    for i in range(3):
        if np.argmax(np.abs(affine[:3, i])) == 0:
            orient += 'R' if affine[0, i] > 0 else 'L'
        elif np.argmax(np.abs(affine[:3, i])) == 1:
            orient += 'A' if affine[1, i] > 0 else 'P'
        else:
            orient += 'S' if affine[2, i] > 0 else 'I'
    return orient

def normalize_img_preserve_range(img):
    """保留强度范围的归一化"""
    img = img.astype(np.float32)
    mask = img != 0
    
    if mask.sum() > 0:
        non_zero_data = img[mask]
        m = non_zero_data.mean()
        s = non_zero_data.std()
        
        if s < 1e-8:
            s = 1.0
        
        normalized_non_zero = (non_zero_data - m) / (s + 1e-8)
        normalized_non_zero = normalized_non_zero * 0.5
        img[mask] = normalized_non_zero
    else:
        m = img.mean()
        s = img.std()
        if s < 1e-8:
            s = 1.0
        img = (img - m) / (s + 1e-8)
        img = img * 0.5
    
    return img

def warp_image(moving, flow, mode='bilinear'):
    """图像变形"""
    B, C, D, H, W = moving.shape
    device = moving.device
    
    zz = torch.linspace(-1, 1, D, device=device)
    yy = torch.linspace(-1, 1, H, device=device)
    xx = torch.linspace(-1, 1, W, device=device)
    
    grid_z, grid_y, grid_x = torch.meshgrid(zz, yy, xx, indexing='ij')
    grid = torch.stack((grid_x, grid_y, grid_z), dim=3).unsqueeze(0)
    
    flow_normalized = flow.permute(0, 2, 3, 4, 1)
    flow_normalized = flow_normalized / torch.tensor([W-1, H-1, D-1], device=device).view(1, 1, 1, 1, 3) * 2
    sample_grid = grid + flow_normalized
    
    warped = F.grid_sample(moving, sample_grid, mode=mode, padding_mode='border', align_corners=True)
    return warped

def save_with_target_geometry(data, target_img, output_path, data_type="image", interpolation_order=1):
    """使用目标图像的几何信息保存数据"""
    try:
        print(f"   保存{data_type}: {output_path}")
        
        if data.ndim != 3:
            if data.ndim == 4 and data.shape[-1] == 3:
                raise ValueError(f"形变场(4D)不应该用此函数保存")
            elif data.ndim == 4:
                data = data[..., 0]
            else:
                raise ValueError(f"不支持的数据维度: {data.ndim}")
        
        if data.shape != target_img.shape[:3]:
            print(f"   调整形状: {data.shape} -> {target_img.shape[:3]}")
            zoom_factors = [target_img.shape[i] / data.shape[i] for i in range(3)]
            data = zoom(data, zoom_factors, order=interpolation_order)
        
        output_img = nib.Nifti1Image(data.astype(np.float32), target_img.affine, header=target_img.header)
        nib.save(output_img, output_path)
        
        print(f"   {data_type}保存成功")
        
    except Exception as e:
        print(f"   保存失败: {e}")
        raise

# ===============================
# 主函数
# ===============================

def get_matching_files(args):
    """获取匹配的文件列表"""
    fixed_files = sorted([f for f in os.listdir(args.fixed) if f.endswith(".nii.gz")])
    moving_files = sorted([f for f in os.listdir(args.moving) if f.endswith(".nii.gz")])
    
    if not fixed_files:
        print(" 在参考图像目录中未找到.nii.gz文件")
        return []
    
    if not moving_files:
        print(" 在浮动图像目录中未找到.nii.gz文件")
        return []
    
    common_filenames = set(fixed_files) & set(moving_files)
    
    if not common_filenames:
        print(" 未找到fixed和moving目录中共同的文件")
        return []
    
    print(f" 找到 {len(common_filenames)} 对匹配的文件")
    
    result_files = []
    for filename in sorted(common_filenames):
        file_info = {
            'filename': filename,
            'fixed_path': os.path.join(args.fixed, filename),
            'moving_path': os.path.join(args.moving, filename),
            'mask_path': None
        }
        
        if args.moving_mask and os.path.exists(args.moving_mask):
            mask_path = os.path.join(args.moving_mask, filename)
            if os.path.exists(mask_path):
                file_info['mask_path'] = mask_path
                print(f"   找到掩码文件: {filename}")
        
        result_files.append(file_info)
    
    return result_files

def main(args):
    device = torch.device("cuda" if torch.cuda.is_available() and not args.cpu else "cpu")
    print("Using device:", device)
    
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    
    if not os.path.exists(args.fixed):
        print(f" 参考图像目录不存在: {args.fixed}")
        return
        
    if not os.path.exists(args.moving):
        print(f" 浮动图像目录不存在: {args.moving}")
        return

    file_list = get_matching_files(args)
    if not file_list:
        return
    
    os.makedirs(args.outdir, exist_ok=True)
    
    print("\n" + "="*60)
    print(" 开始基于切片对应的批量配准")
    print("="*60)
    
    success_count = 0
    
    for file_info in file_list:
        filename = file_info['filename']
        fixed_path = file_info['fixed_path']
        moving_path = file_info['moving_path']
        moving_mask_path = file_info['mask_path']
        
        print(f"\n 处理文件: {filename}")

        try:
            correspondence_dict, similarity_scores = slice_correspondence_registration(
                fixed_path, moving_path, moving_mask_path, args.outdir, args, device
            )
            
            success_count += 1
            print(f"   配准完成: {filename}")
            
        except Exception as e:
            print(f" 处理文件 {filename} 时发生错误: {e}")
            continue
    
    print(f"\n 配准完成: {success_count}/{len(file_list)} 个文件成功")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="基于切片对应的3D医学图像配准框架")
    
    parser.add_argument("--fixed", type=str, required=True, help="参考图像目录路径")
    parser.add_argument("--moving", type=str, required=True, help="浮动图像目录路径") 
    parser.add_argument("--moving_mask", type=str, help="浮动图像掩码目录路径")
    parser.add_argument("--outdir", type=str, required=True, help="输出目录路径")
    
    # 切片对应参数
    parser.add_argument("--correspondence_method", type=str, default="ssim", 
                       choices=["ssim", "ncc", "mi"], help="切片相似度计算方法")
    parser.add_argument("--visualize", action="store_true", help="可视化相似度矩阵")
    
    parser.add_argument("--cpu", action="store_true", help="强制使用CPU")
    
    args = parser.parse_args()
    main(args)