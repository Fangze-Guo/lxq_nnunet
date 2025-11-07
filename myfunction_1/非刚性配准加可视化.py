#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
精简版3D医学图像配准框架 - 支持帧对应匹配
===========================================
- 支持两个图像序列的帧对应匹配
- 简化的配准流程
- 保持核心功能
"""

import os
import argparse
from pathlib import Path
import numpy as np
import nibabel as nib
import SimpleITK as sitk
import torch
import torch.nn as nn
import torch.nn.functional as F
from scipy.ndimage import zoom
from tqdm import trange
import matplotlib.pyplot as plt

# ===============================
# 帧对应匹配函数
# ===============================

def find_frame_correspondence(fixed_volume, moving_volume, fixed_mask=None, moving_mask=None):
    """
    找到两个3D体积序列中帧的最佳对应关系
    
    参数:
        fixed_volume: 参考图像序列 [T, H, W, D] 或 [H, W, D, T]
        moving_volume: 浮动图像序列 [T, H, W, D] 或 [H, W, D, T]
        fixed_mask: 参考图像掩码 (可选)
        moving_mask: 浮动图像掩码 (可选)
    
    返回:
        correspondence: 对应关系列表 [(fixed_idx, moving_idx, similarity_score)]
    """
    print("  🔍 寻找帧对应关系...")
    
    # 确定时间维度
    if fixed_volume.ndim == 4:
        if fixed_volume.shape[0] < fixed_volume.shape[-1]:  # 假设时间在最后一维
            fixed_volume = np.moveaxis(fixed_volume, -1, 0)
        if moving_volume.ndim == 4:
            if moving_volume.shape[0] < moving_volume.shape[-1]:
                moving_volume = np.moveaxis(moving_volume, -1, 0)
    
    fixed_frames = fixed_volume.shape[0] if fixed_volume.ndim == 4 else 1
    moving_frames = moving_volume.shape[0] if moving_volume.ndim == 4 else 1
    
    print(f"    参考图像帧数: {fixed_frames}")
    print(f"    浮动图像帧数: {moving_frames}")
    
    # 如果是单帧图像，直接返回一对一对应
    if fixed_frames == 1 and moving_frames == 1:
        return [(0, 0, 1.0)]
    
    # 计算帧间相似度矩阵
    similarity_matrix = np.zeros((fixed_frames, moving_frames))
    
    for i in range(fixed_frames):
        fixed_frame = fixed_volume[i] if fixed_frames > 1 else fixed_volume
        fixed_frame = normalize_frame(fixed_frame)
        
        for j in range(moving_frames):
            moving_frame = moving_volume[j] if moving_frames > 1 else moving_volume
            moving_frame = normalize_frame(moving_frame)
            
            # 计算归一化互相关 (NCC)
            similarity = calculate_ncc(fixed_frame, moving_frame)
            similarity_matrix[i, j] = similarity
    
    # 找到最佳对应关系
    correspondence = []
    
    if fixed_frames <= moving_frames:
        # 为每个fixed帧找到最匹配的moving帧
        for i in range(fixed_frames):
            best_j = np.argmax(similarity_matrix[i])
            best_score = similarity_matrix[i, best_j]
            correspondence.append((i, best_j, best_score))
    else:
        # 为每个moving帧找到最匹配的fixed帧
        for j in range(moving_frames):
            best_i = np.argmax(similarity_matrix[:, j])
            best_score = similarity_matrix[best_i, j]
            correspondence.append((best_i, j, best_score))
    
    # 打印对应结果
    print("  📊 帧对应结果:")
    for fixed_idx, moving_idx, score in correspondence:
        print(f"    参考帧 {fixed_idx} <-> 浮动帧 {moving_idx} (相似度: {score:.3f})")
    
    return correspondence

def normalize_frame(frame):
    """归一化单帧图像"""
    frame = frame.astype(np.float32)
    if np.any(frame != 0):
        non_zero = frame[frame != 0]
        if non_zero.std() > 1e-8:
            frame = (frame - non_zero.mean()) / non_zero.std()
    return frame

def calculate_ncc(img1, img2):
    """计算归一化互相关"""
    img1_flat = img1.flatten()
    img2_flat = img2.flatten()
    
    # 只考虑非零区域
    mask = (img1_flat != 0) & (img2_flat != 0)
    if np.sum(mask) == 0:
        return 0.0
    
    img1_masked = img1_flat[mask]
    img2_masked = img2_flat[mask]
    
    ncc = np.corrcoef(img1_masked, img2_masked)[0, 1]
    return ncc if not np.isnan(ncc) else 0.0

# ===============================
# 核心配准网络
# ===============================

class ConvBlock(nn.Module):
    def __init__(self, in_ch, out_ch):
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv3d(in_ch, out_ch, 3, padding=1),
            nn.InstanceNorm3d(out_ch),
            nn.LeakyReLU(0.2, inplace=True),
            nn.Conv3d(out_ch, out_ch, 3, padding=1),
            nn.InstanceNorm3d(out_ch),
            nn.LeakyReLU(0.2, inplace=True)
        )
    def forward(self, x):
        return self.conv(x)

class VoxelMorphUNet(nn.Module):
    def __init__(self, in_channels=2):
        super().__init__()
        self.enc1 = ConvBlock(in_channels, 8)
        self.enc2 = ConvBlock(8, 16)
        self.enc3 = ConvBlock(16, 32)
        self.enc4 = ConvBlock(32, 64)
        self.dec3 = ConvBlock(64 + 32, 32)
        self.dec2 = ConvBlock(32 + 16, 16)
        self.dec1 = ConvBlock(16 + 8, 8)
        
        self.flow = nn.Sequential(
            nn.Conv3d(8, 4, 3, padding=1),
            nn.LeakyReLU(0.2, inplace=True),
            nn.Conv3d(4, 3, 3, padding=1),
            nn.Tanh()
        )
        
        self.pool = nn.MaxPool3d(2)
        self.upsample = nn.Upsample(scale_factor=2, mode='trilinear', align_corners=True)

    def forward(self, moving, fixed):
        x = torch.cat([moving, fixed], dim=1)
        
        input_shape = x.shape[2:]
        
        e1 = self.enc1(x)
        e2 = self.enc2(self.pool(e1))
        e3 = self.enc3(self.pool(e2))
        e4 = self.enc4(self.pool(e3))

        d3_up = self.upsample(e4)
        if d3_up.shape[2:] != e3.shape[2:]:
            d3_up = F.interpolate(d3_up, size=e3.shape[2:], mode='trilinear', align_corners=True)
        d3 = self.dec3(torch.cat([d3_up, e3], dim=1))

        d2_up = self.upsample(d3)
        if d2_up.shape[2:] != e2.shape[2:]:
            d2_up = F.interpolate(d2_up, size=e2.shape[2:], mode='trilinear', align_corners=True)
        d2 = self.dec2(torch.cat([d2_up, e2], dim=1))

        d1_up = self.upsample(d2)
        if d1_up.shape[2:] != e1.shape[2:]:
            d1_up = F.interpolate(d1_up, size=e1.shape[2:], mode='trilinear', align_corners=True)
        d1 = self.dec1(torch.cat([d1_up, e1], dim=1))

        flow = self.flow(d1)
        flow = flow * 0.5  # 限制形变范围
        
        if flow.shape[2:] != input_shape:
            flow = F.interpolate(flow, size=input_shape, mode='trilinear', align_corners=True)
        
        return flow

def lncc_loss(I, J, win=[9, 9, 9], eps=1e-5):
    """局部归一化互相关损失"""
    sum_filt = torch.ones([1, 1, *win], device=I.device, dtype=I.dtype)
    pad_no = win[0] // 2
    
    I_sum = F.conv3d(I, sum_filt, stride=1, padding=pad_no)
    J_sum = F.conv3d(J, sum_filt, stride=1, padding=pad_no)
    I2_sum = F.conv3d(I * I, sum_filt, stride=1, padding=pad_no)
    J2_sum = F.conv3d(J * J, sum_filt, stride=1, padding=pad_no)
    IJ_sum = F.conv3d(I * J, sum_filt, stride=1, padding=pad_no)
    
    win_size = np.prod(win)
    u_I = I_sum / win_size
    u_J = J_sum / win_size
    
    cross = IJ_sum - u_J * I_sum - u_I * J_sum + u_I * u_J * win_size
    I_var = I2_sum - 2 * u_I * I_sum + u_I * u_I * win_size
    J_var = J2_sum - 2 * u_J * J_sum + u_J * u_J * win_size
    
    cc = (cross * cross) / (I_var * J_var + eps)
    return -torch.mean(cc)

def gradient_loss(flow):
    """梯度平滑损失"""
    dx = torch.abs(flow[:, :, 1:, :, :] - flow[:, :, :-1, :, :])
    dy = torch.abs(flow[:, :, :, 1:, :] - flow[:, :, :, :-1, :])
    dz = torch.abs(flow[:, :, :, :, 1:] - flow[:, :, :, :, :-1])
    return (dx.mean() + dy.mean() + dz.mean()) / 3.0

def create_identity_grid(shape, device):
    """创建单位网格"""
    D, H, W = shape
    zz = torch.linspace(-1, 1, steps=D, device=device)
    yy = torch.linspace(-1, 1, steps=H, device=device) 
    xx = torch.linspace(-1, 1, steps=W, device=device)
    
    grid_z, grid_y, grid_x = torch.meshgrid(zz, yy, xx, indexing='ij')
    grid = torch.stack((grid_x, grid_y, grid_z), dim=3)
    return grid

def warp_image(moving, flow, mode='bilinear'):
    """图像变形"""
    B, C, D, H, W = flow.shape
    device = flow.device
    
    fx = flow[:, 0] / ((W - 1) / 4.0)
    fy = flow[:, 1] / ((H - 1) / 4.0)
    fz = flow[:, 2] / ((D - 1) / 4.0)
    
    id_grid = create_identity_grid((D, H, W), device).unsqueeze(0)
    disp = torch.stack([fx, fy, fz], dim=4)
    
    sample_grid = id_grid + disp
    warped = F.grid_sample(moving, sample_grid, mode=mode, padding_mode='border', align_corners=True)
    return warped

# ===============================
# 数据处理函数
# ===============================

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

def resample_to_same_shape(fixed, moving):
    """重采样到相同形状"""
    if fixed.shape != moving.shape:
        zoom_factors = [
            fixed.shape[0] / moving.shape[0],
            fixed.shape[1] / moving.shape[1],
            fixed.shape[2] / moving.shape[2]
        ]
        moving = zoom(moving, zoom_factors, order=1)
    return moving

def load_nifti_as_4d(filepath):
    """加载NIfTI文件并确保4D格式"""
    img = nib.load(filepath)
    data = img.get_fdata(dtype=np.float32)
    
    # 确保是4D [T, H, W, D] 格式
    if data.ndim == 3:
        data = data[np.newaxis, ...]  # 添加时间维度
    elif data.ndim == 4:
        # 检查时间维度位置，通常应该在最后一维
        if data.shape[0] < data.shape[-1]:
            data = np.moveaxis(data, -1, 0)
    
    return data, img.affine

# ===============================
# 主配准流程
# ===============================

def register_frame_pair(fixed_frame, moving_frame, device, args):
    """配准单帧图像对"""
    # 预处理
    fixed_n = normalize_img_preserve_range(fixed_frame)
    moving_n = normalize_img_preserve_range(moving_frame)
    
    # 重采样到相同形状
    moving_n = resample_to_same_shape(fixed_n, moving_n)
    
    # 转换为PyTorch张量
    F_t = torch.from_numpy(fixed_n).unsqueeze(0).unsqueeze(0).to(device)
    M_t = torch.from_numpy(moving_n).unsqueeze(0).unsqueeze(0).to(device)
    
    # 训练模型
    model = VoxelMorphUNet().to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr, weight_decay=1e-5)
    
    best_loss = float('inf')
    best_warped = None
    best_flow = None
    
    pbar = trange(args.iterations, desc="配准训练")
    for i in pbar:
        model.train()
        optimizer.zero_grad()
        
        flow = model(M_t, F_t)
        warped = warp_image(M_t, flow)
        
        # 计算损失
        similarity_loss = lncc_loss(warped, F_t)
        smooth_loss = gradient_loss(flow)
        total_loss = similarity_loss + args.smooth_lambda * smooth_loss
        
        total_loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()
        
        pbar.set_postfix({
            'loss': f'{total_loss.item():.4f}',
            'sim': f'{similarity_loss.item():.4f}',
            'smooth': f'{smooth_loss.item():.4f}'
        })
        
        if total_loss.item() < best_loss:
            best_loss = total_loss.item()
            best_warped = warped.detach().clone()
            best_flow = flow.detach().clone()
    
    # 返回最佳结果
    warped_np = best_warped.cpu().numpy().squeeze()
    flow_np = best_flow.cpu().numpy().squeeze()
    
    return warped_np, flow_np, best_loss

def save_registration_result(data, affine, output_path, description="结果"):
    """保存配准结果"""
    try:
        # 确保数据是3D
        if data.ndim == 4 and data.shape[0] == 1:
            data = data[0]
        
        img = nib.Nifti1Image(data.astype(np.float32), affine)
        nib.save(img, output_path)
        print(f"  ✅ {description}保存成功: {output_path}")
    except Exception as e:
        print(f"  ❌ {description}保存失败: {e}")

# ===============================
# 批量配准主函数
# ===============================

def main(args):
    device = torch.device("cuda" if torch.cuda.is_available() and not args.cpu else "cpu")
    print(f"使用设备: {device}")
    
    # 加载图像数据
    print("📥 加载图像数据...")
    fixed_data, fixed_affine = load_nifti_as_4d(args.fixed)
    moving_data, moving_affine = load_nifti_as_4d(args.moving)
    
    print(f"参考图像形状: {fixed_data.shape}")
    print(f"浮动图像形状: {moving_data.shape}")
    
    # 寻找帧对应关系
    correspondence = find_frame_correspondence(fixed_data, moving_data)
    
    # 创建输出目录
    os.makedirs(args.outdir, exist_ok=True)
    
    # 对每对对应帧进行配准
    print("\n🎯 开始批量配准...")
    results = []
    
    for fixed_idx, moving_idx, similarity in correspondence:
        print(f"\n🔧 配准对: 参考帧 {fixed_idx} <-> 浮动帧 {moving_idx}")
        
        # 提取对应帧
        fixed_frame = fixed_data[fixed_idx] if fixed_data.shape[0] > 1 else fixed_data[0]
        moving_frame = moving_data[moving_idx] if moving_data.shape[0] > 1 else moving_data[0]
        
        # 执行配准
        try:
            warped, flow, loss = register_frame_pair(
                fixed_frame, moving_frame, device, args
            )
            
            # 保存结果
            base_name = f"pair_{fixed_idx}_{moving_idx}"
            
            # 保存配准后的图像
            warped_path = os.path.join(args.outdir, f"{base_name}_warped.nii.gz")
            save_registration_result(warped, fixed_affine, warped_path, "配准图像")
            
            # 保存形变场
            flow_path = os.path.join(args.outdir, f"{base_name}_flow.nii.gz")
            save_registration_result(flow, fixed_affine, flow_path, "形变场")
            
            results.append({
                'fixed_idx': fixed_idx,
                'moving_idx': moving_idx,
                'similarity': similarity,
                'loss': loss,
                'warped_path': warped_path,
                'flow_path': flow_path
            })
            
            print(f"  ✅ 配准完成, 损失: {loss:.4f}")
            
        except Exception as e:
            print(f"  ❌ 配准失败: {e}")
            continue
    
    # 输出总结报告
    print("\n" + "="*50)
    print("📊 配准总结报告")
    print("="*50)
    print(f"总配准对数: {len(results)}/{len(correspondence)}")
    
    if results:
        avg_loss = np.mean([r['loss'] for r in results])
        avg_similarity = np.mean([r['similarity'] for r in results])
        print(f"平均损失: {avg_loss:.4f}")
        print(f"平均初始相似度: {avg_similarity:.3f}")
        print(f"输出目录: {args.outdir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="精简版3D医学图像配准框架")
    
    # 输入输出参数
    parser.add_argument("--fixed", type=str, required=True, help="参考图像路径")
    parser.add_argument("--moving", type=str, required=True, help="浮动图像路径")
    parser.add_argument("--outdir", type=str, required=True, help="输出目录路径")
    
    # 配准参数
    parser.add_argument("--iterations", type=int, default=1000, help="配准迭代次数")
    parser.add_argument("--lr", type=float, default=1e-4, help="学习率")
    parser.add_argument("--smooth_lambda", type=float, default=0.5, help="平滑项权重")
    
    # 设备参数
    parser.add_argument("--cpu", action="store_true", help="强制使用CPU")
    
    args = parser.parse_args()
    
    main(args)