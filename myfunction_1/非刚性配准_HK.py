#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复版增强稳健3D MRI医学图像配准（GPU版）- 轻量版本：
- 减少网络参数量，防止显存崩溃
- 修复跳跃连接中的尺寸匹配问题
- 增强的尺寸匹配和稳健性处理
- 支持限制处理病例数量
"""

import os
from pathlib import Path
import argparse
import numpy as np
import SimpleITK as sitk
import nibabel as nib
import torch
import torch.nn as nn
import torch.nn.functional as F

# ===============================
# 辅助函数（增强稳健性版本）
# ===============================

def safe_divide(numerator, denominator, default=0.0):
    """安全的除法操作，防止除零错误"""
    if isinstance(numerator, torch.Tensor) and isinstance(denominator, torch.Tensor):
        return torch.where(
            denominator.abs() > 1e-10, 
            numerator / denominator, 
            torch.tensor(default, device=numerator.device, dtype=numerator.dtype)
        )
    else:
        if np.abs(denominator) < 1e-10:
            return default
        return numerator / denominator

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
    return safe_divide(intersection, fixed_nonzero.sum())

def n4_correction(sitk_img):
    try:
        mask = sitk.OtsuThreshold(sitk_img, 0, 1, 200)
        corrector = sitk.N4BiasFieldCorrectionImageFilter()
        out = corrector.Execute(sitk_img, mask)
        return out
    except Exception as e:
        print("  ⚠️ N4 bias correction failed:", e)
        return sitk_img

def percentile_normalize_np(arr, pmin=1, pmax=99):
    """增强的百分位归一化，包含安全检查"""
    if arr.size == 0:
        return np.zeros_like(arr)
    
    lo = np.percentile(arr, pmin)
    hi = np.percentile(arr, pmax)
    arr = np.clip(arr, lo, hi)
    
    if np.abs(hi - lo) < 1e-10:
        return np.zeros_like(arr)
    
    return safe_divide(arr - lo, hi - lo)

def torch_to_sitk(img_tensor, reference_img):
    arr = img_tensor.squeeze().detach().cpu().numpy()
    sitk_img = sitk.GetImageFromArray(arr)
    sitk_img.CopyInformation(reference_img)
    return sitk_img

def resize_tensor(tensor, target_size):
    """调整张量尺寸到目标大小"""
    return F.interpolate(tensor, size=target_size, mode='trilinear', align_corners=True)

class LightUNet3D(nn.Module):
    def __init__(self, in_ch=2, out_ch=3, f=16):  # 减少基础通道数
        """
        轻量版3D UNet架构，减少参数量
        """
        super().__init__()
        
        # 编码器路径 (下采样) - 减少层数和通道数
        self.enc1 = nn.Sequential(
            nn.Conv3d(in_ch, f, 3, 1, 1),
            nn.BatchNorm3d(f),
            nn.ReLU(inplace=True),
            nn.Conv3d(f, f, 3, 1, 1),
            nn.BatchNorm3d(f),
            nn.ReLU(inplace=True)
        )
        
        self.pool1 = nn.MaxPool3d(2)
        
        self.enc2 = nn.Sequential(
            nn.Conv3d(f, f*2, 3, 1, 1),
            nn.BatchNorm3d(f*2),
            nn.ReLU(inplace=True),
            nn.Conv3d(f*2, f*2, 3, 1, 1),
            nn.BatchNorm3d(f*2),
            nn.ReLU(inplace=True)
        )
        
        self.pool2 = nn.MaxPool3d(2)
        
        self.enc3 = nn.Sequential(
            nn.Conv3d(f*2, f*4, 3, 1, 1),
            nn.BatchNorm3d(f*4),
            nn.ReLU(inplace=True),
            nn.Conv3d(f*4, f*4, 3, 1, 1),
            nn.BatchNorm3d(f*4),
            nn.ReLU(inplace=True)
        )
        
        self.pool3 = nn.MaxPool3d(2)
        
        # 移除一层编码层，减少深度
        
        # 瓶颈层 - 减少通道数
        self.bottleneck = nn.Sequential(
            nn.Conv3d(f*4, f*8, 3, 1, 1),
            nn.BatchNorm3d(f*8),
            nn.ReLU(inplace=True),
            nn.Conv3d(f*8, f*8, 3, 1, 1),
            nn.BatchNorm3d(f*8),
            nn.ReLU(inplace=True)
        )
        
        # 解码器路径 (上采样) - 对应减少层数
        self.up3 = nn.ConvTranspose3d(f*8, f*4, 2, 2)
        self.dec3 = nn.Sequential(
            nn.Conv3d(f*8, f*4, 3, 1, 1),  # 通道数减半
            nn.BatchNorm3d(f*4),
            nn.ReLU(inplace=True),
            nn.Conv3d(f*4, f*4, 3, 1, 1),
            nn.BatchNorm3d(f*4),
            nn.ReLU(inplace=True)
        )
        
        self.up2 = nn.ConvTranspose3d(f*4, f*2, 2, 2)
        self.dec2 = nn.Sequential(
            nn.Conv3d(f*4, f*2, 3, 1, 1),
            nn.BatchNorm3d(f*2),
            nn.ReLU(inplace=True),
            nn.Conv3d(f*2, f*2, 3, 1, 1),
            nn.BatchNorm3d(f*2),
            nn.ReLU(inplace=True)
        )
        
        self.up1 = nn.ConvTranspose3d(f*2, f, 2, 2)
        self.dec1 = nn.Sequential(
            nn.Conv3d(f*2, f, 3, 1, 1),
            nn.BatchNorm3d(f),
            nn.ReLU(inplace=True),
            nn.Conv3d(f, f, 3, 1, 1),
            nn.BatchNorm3d(f),
            nn.ReLU(inplace=True)
        )
        
        # 输出层
        self.out_conv = nn.Conv3d(f, out_ch, 3, 1, 1)
        
        self._initialize_weights()
    
    def _initialize_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Conv3d):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.BatchNorm3d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
    
    def forward(self, x):
        # 编码路径
        e1 = self.enc1(x)          # [B, f, D, H, W]
        e2 = self.enc2(self.pool1(e1))  # [B, f*2, D/2, H/2, W/2]
        e3 = self.enc3(self.pool2(e2))  # [B, f*4, D/4, H/4, W/4]
        
        # 瓶颈
        b = self.bottleneck(self.pool3(e3))  # [B, f*8, D/8, H/8, W/8]
        
        # 解码路径 + 跳跃连接（带尺寸匹配）
        d3 = self.up3(b)  # [B, f*4, D/4, H/4, W/4]
        d3 = self._match_size(d3, e3)
        d3 = self.dec3(torch.cat([d3, e3], dim=1))  # [B, f*4, D/4, H/4, W/4]
        
        d2 = self.up2(d3)  # [B, f*2, D/2, H/2, W/2]
        d2 = self._match_size(d2, e2)
        d2 = self.dec2(torch.cat([d2, e2], dim=1))  # [B, f*2, D/2, H/2, W/2]
        
        d1 = self.up1(d2)  # [B, f, D, H, W]
        d1 = self._match_size(d1, e1)
        d1 = self.dec1(torch.cat([d1, e1], dim=1))  # [B, f, D, H, W]
        
        out = self.out_conv(d1)
        return out
    
    def _match_size(self, tensor1, tensor2):
        """确保两个张量在空间维度上尺寸一致"""
        if tensor1.shape[2:] != tensor2.shape[2:]:
            # 使用插值调整尺寸
            return F.interpolate(tensor1, size=tensor2.shape[2:], mode='trilinear', align_corners=True)
        return tensor1

def warp_image(moving, flow):
    """
    moving: [B,1,D,H,W]
    flow: [B,3,D,H,W], voxel displacement
    returns: warped image [B,1,D,H,W]
    """
    B, C, D, H, W = moving.shape
    device = moving.device

    z = torch.linspace(-1,1,D,device=device)
    y = torch.linspace(-1,1,H,device=device)
    x = torch.linspace(-1,1,W,device=device)
    zz,yy,xx = torch.meshgrid(z,y,x,indexing='ij')
    grid = torch.stack((xx,yy,zz), dim=-1)
    grid = grid.unsqueeze(0).repeat(B,1,1,1,1)

    flow_norm = torch.zeros_like(flow)
    
    W_factor = safe_divide(1.0, (W-1)/2, default=0.0)
    H_factor = safe_divide(1.0, (H-1)/2, default=0.0) 
    D_factor = safe_divide(1.0, (D-1)/2, default=0.0)
    
    flow_norm[:,0] = flow[:,0] * W_factor
    flow_norm[:,1] = flow[:,1] * H_factor  
    flow_norm[:,2] = flow[:,2] * D_factor
    
    flow_norm = flow_norm.permute(0,2,3,4,1)

    warped = F.grid_sample(moving, grid + flow_norm, align_corners=True, mode='bilinear', padding_mode='border')
    return warped

# ===============================
# 局部 NCC 损失
# ===============================
class LocalNCC(nn.Module):
    def __init__(self, win=7, eps=1e-5):  # 减小窗口大小
        super().__init__()
        self.win = win
        self.eps = eps

    def forward(self, I, J):
        conv = F.conv3d
        win = self.win
        filt = torch.ones((1,1,win,win,win), device=I.device)
        I2, J2, IJ = I*I, J*J, I*J
        sumI = conv(I, filt, padding=win//2)
        sumJ = conv(J, filt, padding=win//2)
        sumI2 = conv(I2, filt, padding=win//2)
        sumJ2 = conv(J2, filt, padding=win//2)
        sumIJ = conv(IJ, filt, padding=win//2)
        win_size = win**3
        
        uI = safe_divide(sumI, win_size)
        uJ = safe_divide(sumJ, win_size)
        
        cross = sumIJ - uJ*sumI - uI*sumJ + uI*uJ*win_size
        varI = sumI2 - 2*uI*sumI + uI*uI*win_size
        varJ = sumJ2 - 2*uJ*sumJ + uJ*uJ*win_size
        
        denominator = varI * varJ + self.eps
        cc = safe_divide(cross * cross, denominator)
        
        return -torch.mean(cc)

# ===============================
# 稳健的配准流程
# ===============================

def robust_rigid_registration(fixed_img, moving_img, filename):
    """增强稳健性的刚性配准"""
    try:
        print(f"  🔧 开始刚性配准: {filename}")
        
        fixed_stats = image_stats(fixed_img)
        moving_stats = image_stats(moving_img)
        print(f"    参考图像统计: min={fixed_stats[0]:.3f}, max={fixed_stats[1]:.3f}, mean={fixed_stats[2]:.3f}")
        print(f"    浮动图像统计: min={moving_stats[0]:.3f}, max={moving_stats[1]:.3f}, mean={moving_stats[2]:.3f}")
        
        if fixed_stats[4] < 10 or moving_stats[4] < 10:
            print("  ⚠️ 图像非零像素太少，跳过刚性配准")
            return moving_img
        
        rigid_method = sitk.ImageRegistrationMethod()
        rigid_method.SetMetricAsMattesMutualInformation(numberOfHistogramBins=50)
        rigid_method.SetOptimizerAsGradientDescent(learningRate=1.0, numberOfIterations=100)  # 减少迭代次数
        rigid_method.SetOptimizerScalesFromPhysicalShift()
        rigid_method.SetInterpolator(sitk.sitkLinear)
        
        try:
            initial_rigid = sitk.CenteredTransformInitializer(
                fixed_img, moving_img, sitk.Euler3DTransform(), 
                sitk.CenteredTransformInitializerFilter.MOMENTS
            )
        except:
            print("  ⚠️ 中心初始化失败，使用几何中心初始化")
            initial_rigid = sitk.CenteredTransformInitializer(
                fixed_img, moving_img, sitk.Euler3DTransform(), 
                sitk.CenteredTransformInitializerFilter.GEOMETRY
            )
            
        rigid_method.SetInitialTransform(initial_rigid, inPlace=False)
        rigid_transform = rigid_method.Execute(fixed_img, moving_img)
        moved_rigid = sitk.Resample(moving_img, fixed_img, rigid_transform, sitk.sitkLinear, 0.0, moving_img.GetPixelID())
        
        overlap = compute_overlap_fraction(fixed_img, moved_rigid)
        print(f"  📊 刚性配准后重叠度: {overlap:.3f}")
        
        return moved_rigid
        
    except Exception as e:
        print(f"  ❌ 刚性配准失败: {e}")
        print("  ⚠️ 返回原始图像进行后续处理")
        return moving_img

def nonrigid_registration_gpu(fixed_img, moved_rigid, filename, device):
    """GPU非刚性配准 - 轻量版本"""
    try:
        print(f"  🧠 开始非刚性配准: {filename}")
        
        # 偏置场校正
        fixed_n4 = n4_correction(fixed_img)
        moved_n4 = n4_correction(moved_rigid)

        # 归一化处理
        fixed_np = percentile_normalize_np(sitk.GetArrayFromImage(fixed_n4))
        moved_np = percentile_normalize_np(sitk.GetArrayFromImage(moved_n4))
        
        # 检查数据有效性
        if np.all(fixed_np == 0) or np.all(moved_np == 0):
            print("  ⚠️ 归一化后图像全为零，跳过非刚性配准")
            return moved_rigid

        # 下采样以减少显存使用
        original_size = fixed_np.shape
        target_size = tuple(max(32, dim // 2) for dim in original_size)  # 至少32，最大减半
        
        # torch tensor [1,1,D,H,W] - 使用更小的尺寸
        fixed_t = torch.from_numpy(fixed_np).unsqueeze(0).unsqueeze(0).float().to(device)
        moving_t = torch.from_numpy(moved_np).unsqueeze(0).unsqueeze(0).float().to(device)
        
        # 如果图像太大，进行下采样
        if fixed_t.numel() > 256 * 256 * 256:  # 如果体素超过这个数
            target_size = tuple(dim // 2 for dim in fixed_t.shape[2:])
            fixed_t = F.interpolate(fixed_t, size=target_size, mode='trilinear', align_corners=True)
            moving_t = F.interpolate(moving_t, size=target_size, mode='trilinear', align_corners=True)
            print(f"  🔽 图像下采样至: {target_size}")

        # 使用轻量版网络
        model = LightUNet3D(in_ch=2, out_ch=3, f=8).to(device)  # 减少基础通道数
        optimizer = torch.optim.Adam(model.parameters(), lr=1e-4, weight_decay=1e-5)
        scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=15)
        ncc_loss = LocalNCC(win=5)  # 更小的窗口

        # 训练循环 - 减少迭代次数
        model.train()
        best_loss = float('inf')
        patience_counter = 0
        max_patience = 40
        max_iterations = 1000  # 减少最大迭代次数
        
        for iter in range(1, max_iterations + 1):
            optimizer.zero_grad()
            flow = model(torch.cat([moving_t, fixed_t], dim=1))
            moved = warp_image(moving_t, flow)
            loss = ncc_loss(moved, fixed_t)
            
            if torch.isnan(loss) or torch.isinf(loss):
                print(f"  ⚠️ 迭代 {iter} 损失值为 {loss.item()}，跳过此迭代")
                optimizer.zero_grad()
                continue
                
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            scheduler.step(loss)
            
            # 早停机制
            if loss.item() < best_loss:
                best_loss = loss.item()
                patience_counter = 0
                torch.save(model.state_dict(), f'best_model_{filename.split(".")[0]}.pth')
            else:
                patience_counter += 1
                
            if patience_counter >= max_patience:
                print(f"  🛑 早停在迭代 {iter}，最佳损失: {best_loss:.6f}")
                break
                
            if iter % 100 == 0:
                current_lr = optimizer.param_groups[0]['lr']
                print(f"    Iter {iter}/{max_iterations} - Loss: {loss.item():.6f}, LR: {current_lr:.2e}")

        # 加载最佳模型
        try:
            model.load_state_dict(torch.load(f'best_model_{filename.split(".")[0]}.pth'))
            print(f"  ✅ 加载最佳模型完成")
        except:
            print(f"  ⚠️ 无法加载最佳模型，使用最终模型")

        # 最终推理
        with torch.no_grad():
            model.eval()
            flow_final = model(torch.cat([moving_t, fixed_t], dim=1))
            moved_final = warp_image(moving_t, flow_final)
            
        # 如果进行了下采样，需要上采样回原始尺寸
        if moved_final.shape[2:] != original_size:
            moved_final = F.interpolate(moved_final, size=original_size, mode='trilinear', align_corners=True)
            print(f"  🔼 图像上采样回原始尺寸: {original_size}")
            
        registered_img_sitk = torch_to_sitk(moved_final, fixed_img)
        
        # 清理临时文件
        try:
            os.remove(f'best_model_{filename.split(".")[0]}.pth')
        except:
            pass
            
        # 统计结果
        mn, mx, mean, std, nz = image_stats(registered_img_sitk)
        print(f"  📊 非刚性配准结果统计: min={mn:.3f}, max={mx:.3f}, mean={mean:.3f}, std={std:.3f}, nonzero={nz}")
        
        return registered_img_sitk
        
    except Exception as e:
        print(f"  ❌ 非刚性配准失败: {e}")
        import traceback
        traceback.print_exc()
        print("  ⚠️ 返回刚性配准结果")
        return moved_rigid

def main(args):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("Using device:", device)
    
    # 设置GPU内存增长模式，避免一次性分配过多内存
    if torch.cuda.is_available():
        torch.backends.cudnn.benchmark = True
        torch.cuda.empty_cache()
    
    if not os.path.exists(args.fixed):
        print(f"❌ 参考图像目录不存在: {args.fixed}")
        return
        
    if not os.path.exists(args.moving):
        print(f"❌ 浮动图像目录不存在: {args.moving}")
        return

    moving_files = sorted([f for f in os.listdir(args.moving) if f.endswith(".nii") or f.endswith(".nii.gz")])
    if not moving_files:
        print("❌ 在浮动图像目录中未找到.nii或.nii.gz文件")
        return
    
    # 限制处理的病例数量
    if args.num_cases > 0:
        moving_files = moving_files[:args.num_cases]
        print(f"📝 限制处理前 {args.num_cases} 个病例")
    
    os.makedirs(args.outdir, exist_ok=True)
    
    rigid_dir = os.path.join(args.outdir, "rigid_results")
    os.makedirs(rigid_dir, exist_ok=True)
    
    # 阶段1: 刚性配准
    print("\n" + "="*60)
    print("🎯 阶段1: 开始批量刚性配准")
    print("="*60)
    
    rigid_results = {}
    rigid_success_count = 0
    
    for filename in moving_files:
        print("\n" + "-"*50)
        print("🧩 处理文件:", filename)
        print("-"*50)

        moving_path = os.path.join(args.moving, filename)
        fixed_path = os.path.join(args.fixed, filename)
        
        if not os.path.exists(fixed_path):
            print(f"❌ 找不到匹配的参考图像: {fixed_path}")
            print(f"⚠️ 跳过文件: {filename}")
            continue

        try:
            fixed_img = sitk.ReadImage(fixed_path, sitk.sitkFloat32)
            moving_img = sitk.ReadImage(moving_path, sitk.sitkFloat32)
            
            moved_rigid = robust_rigid_registration(fixed_img, moving_img, filename)
            
            rigid_output_path = os.path.join(rigid_dir, Path(filename).stem+"_rigid.nii.gz")
            save_nifti(moved_rigid, rigid_output_path)
            
            rigid_results[filename] = {
                'fixed_img': fixed_img,
                'moved_rigid': moved_rigid,
                'rigid_path': rigid_output_path
            }
            rigid_success_count += 1
            print(f"  ✅ 刚性配准完成: {filename}")
            
        except Exception as e:
            print(f"❌ 处理文件 {filename} 时发生错误: {e}")
            continue
    
    print(f"\n📊 刚性配准阶段完成: {rigid_success_count}/{len(moving_files)} 个文件成功")
    
    if rigid_success_count == 0:
        print("❌ 没有成功完成刚性配准的文件，程序退出")
        return
    
    # 阶段2: 非刚性配准
    print("\n" + "="*60)
    print("🧠 阶段2: 开始批量非刚性配准")
    print("="*60)
    
    nonrigid_success_count = 0
    
    for filename, data in rigid_results.items():
        print("\n" + "-"*50)
        print("🔮 非刚性配准文件:", filename)
        print("-"*50)
        
        try:
            # 在每次处理前清空GPU缓存
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                
            fixed_img = data['fixed_img']
            moved_rigid = data['moved_rigid']
            
            registered_final = nonrigid_registration_gpu(fixed_img, moved_rigid, filename, device)
            
            final_output_path = os.path.join(args.outdir, Path(filename).stem+"_registered.nii.gz")
            save_nifti(registered_final, final_output_path)
            
            nonrigid_success_count += 1
            print(f"  ✅ 非刚性配准完成: {filename}")
            
        except Exception as e:
            print(f"❌ 非刚性配准处理文件 {filename} 时发生错误: {e}")
            continue
    
    print(f"\n📊 非刚性配准阶段完成: {nonrigid_success_count}/{rigid_success_count} 个文件成功")
    
    # 最终统计
    print("\n" + "="*60)
    print("🎯 最终统计报告")
    print("="*60)
    print(f"总文件数: {len(moving_files)}")
    print(f"成功完成刚性配准: {rigid_success_count}")
    print(f"成功完成非刚性配准: {nonrigid_success_count}")
    print(f"输出目录: {args.outdir}")
    print(f"刚性配准中间结果: {rigid_dir}")
    print("="*60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="修复版增强稳健3D医学图像配准（GPU轻量版）")
    parser.add_argument("--fixed", type=str, required=True, help="参考图像目录路径")
    parser.add_argument("--moving", type=str, required=True, help="浮动图像目录路径") 
    parser.add_argument("--outdir", type=str, required=True, help="输出目录路径")
    parser.add_argument("--num_cases", type=int, default=-1, 
                       help="处理的病例数量，-1表示处理所有病例（默认），正整数表示处理前N个病例")
    args = parser.parse_args()
    main(args)

