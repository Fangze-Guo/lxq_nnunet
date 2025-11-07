import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from mpl_toolkits.mplot3d import Axes3D
import nibabel as nib
import os
from pathlib import Path

def comprehensive_deformation_visualization(flow_field_path, fixed_image_path, output_dir, 
                                          slice_idx=None, vector_scale=30, 
                                          density=4, save_formats=['png']):
    """
    综合形变场可视化 - 生成多种可视化图表
    
    参数:
        flow_field_path: 形变场文件路径 (.nii.gz)
        fixed_image_path: 参考图像路径
        output_dir: 输出目录
        slice_idx: 指定切片，None为自动选择
        vector_scale: 向量缩放因子
        density: 向量密度（下采样因子）
        save_formats: 保存格式列表 ['png', 'pdf', 'svg']
    """
    
    # 加载数据
    print("📥 加载形变场和参考图像...")
    flow_field_img = nib.load(flow_field_path)
    fixed_img = nib.load(fixed_image_path)
    
    flow_field = flow_field_img.get_fdata()
    fixed_data = fixed_img.get_fdata()
    
    print(f"形变场形状: {flow_field.shape}")
    print(f"参考图像形状: {fixed_data.shape}")
    
    # 自动选择中间切片
    if slice_idx is None:
        slice_idx = flow_field.shape[2] // 2
    
    filename = Path(flow_field_path).stem.replace('_flow_forward_4d', '')
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. 基础形变场可视化
    basic_viz_path = plot_basic_deformation(flow_field, fixed_data, slice_idx, 
                                          output_dir, filename, save_formats)
    
    # 2. 3D向量场可视化
    vector_3d_path = plot_3d_vector_field(flow_field, slice_idx, vector_scale,
                                        density, output_dir, filename, save_formats)
    
    # 3. 位移分析可视化
    displacement_path = plot_displacement_analysis(flow_field, slice_idx,
                                                 output_dir, filename, save_formats)
    
    # 4. 流线可视化
    streamlines_path = plot_streamlines(flow_field, fixed_data, slice_idx,
                                      output_dir, filename, save_formats)
    
    # 5. 多平面可视化
    multiplanar_path = plot_multiplanar_view(flow_field, fixed_data,
                                           output_dir, filename, save_formats)
    
    print("✅ 形变场可视化完成!")
    return {
        'basic': basic_viz_path,
        '3d_vector': vector_3d_path,
        'displacement': displacement_path,
        'streamlines': streamlines_path,
        'multiplanar': multiplanar_path
    }

def plot_basic_deformation(flow_field, fixed_data, slice_idx, output_dir, filename, save_formats):
    """基础形变场可视化 - 各分量和合成"""
    
    fig = plt.figure(figsize=(20, 12))
    gs = gridspec.GridSpec(2, 4, figure=fig)
    fig.suptitle(f'Basic Deformation Field Visualization - {filename}\nSlice {slice_idx}', 
                 fontsize=16, fontweight='bold')
    
    # 参考图像
    ax1 = fig.add_subplot(gs[0, 0])
    im1 = ax1.imshow(fixed_data[:, :, slice_idx], cmap='gray')
    ax1.set_title('Fixed Image (Reference)')
    ax1.axis('off')
    plt.colorbar(im1, ax=ax1, fraction=0.046)
    
    # X方向形变
    ax2 = fig.add_subplot(gs[0, 1])
    flow_x = flow_field[:, :, slice_idx, 0]
    vmax_x = max(abs(flow_x.min()), abs(flow_x.max()))
    im2 = ax2.imshow(flow_x, cmap='coolwarm', vmin=-vmax_x, vmax=vmax_x)
    ax2.set_title('Deformation - X Direction')
    ax2.axis('off')
    plt.colorbar(im2, ax=ax2, fraction=0.046)
    
    # Y方向形变
    ax3 = fig.add_subplot(gs[0, 2])
    flow_y = flow_field[:, :, slice_idx, 1]
    vmax_y = max(abs(flow_y.min()), abs(flow_y.max()))
    im3 = ax3.imshow(flow_y, cmap='coolwarm', vmin=-vmax_y, vmax=vmax_y)
    ax3.set_title('Deformation - Y Direction')
    ax3.axis('off')
    plt.colorbar(im3, ax=ax3, fraction=0.046)
    
    # Z方向形变
    ax4 = fig.add_subplot(gs[0, 3])
    flow_z = flow_field[:, :, slice_idx, 2]
    vmax_z = max(abs(flow_z.min()), abs(flow_z.max()))
    im4 = ax4.imshow(flow_z, cmap='coolwarm', vmin=-vmax_z, vmax=vmax_z)
    ax4.set_title('Deformation - Z Direction')
    ax4.axis('off')
    plt.colorbar(im4, ax=ax4, fraction=0.046)
    
    # 位移幅度
    ax5 = fig.add_subplot(gs[1, 0])
    magnitude = np.sqrt(flow_x**2 + flow_y**2 + flow_z**2)
    im5 = ax5.imshow(magnitude, cmap='viridis')
    ax5.set_title('Displacement Magnitude')
    ax5.axis('off')
    plt.colorbar(im5, ax=ax5, fraction=0.046)
    
    # 2D向量场（XY平面）
    ax6 = fig.add_subplot(gs[1, 1])
    # 下采样显示向量
    skip = 6
    y, x = np.mgrid[0:flow_field.shape[0]:skip, 0:flow_field.shape[1]:skip]
    u = flow_field[::skip, ::skip, slice_idx, 0]
    v = flow_field[::skip, ::skip, slice_idx, 1]
    
    # 在参考图像上叠加向量
    ax6.imshow(fixed_data[:, :, slice_idx], cmap='gray', alpha=0.7)
    Q = ax6.quiver(x, y, u, v, scale=50, color='red', alpha=0.8, 
                   width=0.003, headwidth=3, headlength=4)
    ax6.quiverkey(Q, 0.9, 0.9, 1, '1 voxel', labelpos='E', coordinates='figure')
    ax6.set_title('Deformation Vectors (XY Plane)')
    ax6.axis('off')
    
    # 位移方向分布
    ax7 = fig.add_subplot(gs[1, 2])
    angles = np.arctan2(flow_y.flatten(), flow_x.flatten())
    ax7.hist(angles, bins=36, alpha=0.7, color='skyblue', edgecolor='black')
    ax7.set_xlabel('Direction Angle (radians)')
    ax7.set_ylabel('Frequency')
    ax7.set_title('Displacement Direction Distribution')
    ax7.grid(True, alpha=0.3)
    
    # 统计信息
    ax8 = fig.add_subplot(gs[1, 3])
    ax8.axis('off')
    stats_text = f"""Deformation Statistics:
X: {flow_x.mean():.3f} ± {flow_x.std():.3f}
Y: {flow_y.mean():.3f} ± {flow_y.std():.3f}  
Z: {flow_z.mean():.3f} ± {flow_z.std():.3f}
Magnitude: {magnitude.mean():.3f} ± {magnitude.std():.3f}
Max: {magnitude.max():.3f}
95%: {np.percentile(magnitude, 95):.3f}"""
    
    ax8.text(0.1, 0.9, stats_text, transform=ax8.transAxes, fontsize=10,
             verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    plt.tight_layout()
    
    # 保存图片
    base_path = os.path.join(output_dir, f"{filename}_basic_deformation_slice{slice_idx}")
    save_plot(fig, base_path, save_formats)
    
    return base_path + '.png'

def plot_3d_vector_field(flow_field, slice_idx, vector_scale, density, output_dir, filename, save_formats):
    """3D向量场可视化"""
    
    try:
        fig = plt.figure(figsize=(15, 10))
        ax = fig.add_subplot(111, projection='3d')
        
        # 下采样
        skip = density
        x, y, z = np.mgrid[0:flow_field.shape[0]:skip, 
                          0:flow_field.shape[1]:skip, 
                          slice_idx:slice_idx+1]
        
        u = flow_field[::skip, ::skip, slice_idx, 0]
        v = flow_field[::skip, ::skip, slice_idx, 1]
        w = flow_field[::skip, ::skip, slice_idx, 2]
        
        # 创建3D向量图
        ax.quiver(x, y, z, u, v, w, 
                 length=vector_scale, normalize=True, 
                 color='red', alpha=0.7, linewidth=1)
        
        ax.set_xlabel('X')
        ax.set_ylabel('Y') 
        ax.set_zlabel('Z')
        ax.set_title(f'3D Deformation Vector Field - {filename}\nSlice {slice_idx}')
        
        # 设置相等的轴比例
        max_range = max(flow_field.shape[0], flow_field.shape[1])
        ax.set_xlim([0, max_range])
        ax.set_ylim([0, max_range])
        ax.set_zlim([slice_idx-5, slice_idx+5])
        
        plt.tight_layout()
        
        base_path = os.path.join(output_dir, f"{filename}_3d_vectors_slice{slice_idx}")
        save_plot(fig, base_path, save_formats)
        
        return base_path + '.png'
        
    except Exception as e:
        print(f"⚠️ 3D可视化失败: {e}")
        return None

def plot_displacement_analysis(flow_field, slice_idx, output_dir, filename, save_formats):
    """位移分析可视化"""
    
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle(f'Displacement Analysis - {filename}\nSlice {slice_idx}', 
                 fontsize=16, fontweight='bold')
    
    # 提取数据
    flow_x = flow_field[:, :, slice_idx, 0]
    flow_y = flow_field[:, :, slice_idx, 1]
    flow_z = flow_field[:, :, slice_idx, 2]
    magnitude = np.sqrt(flow_x**2 + flow_y**2 + flow_z**2)
    
    # 位移幅度热图
    im1 = axes[0, 0].imshow(magnitude, cmap='hot')
    axes[0, 0].set_title('Displacement Magnitude Heatmap')
    axes[0, 0].axis('off')
    plt.colorbar(im1, ax=axes[0, 0], fraction=0.046)
    
    # 位移幅度直方图
    axes[0, 1].hist(magnitude.flatten(), bins=50, alpha=0.7, color='lightcoral', edgecolor='black')
    axes[0, 1].axvline(magnitude.mean(), color='red', linestyle='--', 
                      label=f'Mean: {magnitude.mean():.3f}')
    axes[0, 1].axvline(np.percentile(magnitude, 95), color='blue', linestyle='--',
                      label=f'95%: {np.percentile(magnitude, 95):.3f}')
    axes[0, 1].set_xlabel('Displacement Magnitude (voxels)')
    axes[0, 1].set_ylabel('Frequency')
    axes[0, 1].set_title('Displacement Magnitude Distribution')
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)
    
    # 各方向位移分布
    axes[1, 0].hist(flow_x.flatten(), bins=50, alpha=0.5, label='X', color='red')
    axes[1, 0].hist(flow_y.flatten(), bins=50, alpha=0.5, label='Y', color='green')
    axes[1, 0].hist(flow_z.flatten(), bins=50, alpha=0.5, label='Z', color='blue')
    axes[1, 0].set_xlabel('Displacement (voxels)')
    axes[1, 0].set_ylabel('Frequency')
    axes[1, 0].set_title('Directional Displacement Distribution')
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)
    
    # 位移方向玫瑰图
    angles = np.arctan2(flow_y.flatten(), flow_x.flatten())
    magnitudes_flat = magnitude.flatten()
    
    # 创建方向分箱
    angle_bins = np.linspace(-np.pi, np.pi, 13)
    direction_sums = []
    for i in range(len(angle_bins)-1):
        mask = (angles >= angle_bins[i]) & (angles < angle_bins[i+1])
        if np.any(mask):
            direction_sums.append(np.mean(magnitudes_flat[mask]))
        else:
            direction_sums.append(0)
    
    theta = angle_bins[:-1] + np.pi/12
    radii = direction_sums
    
    ax_polar = fig.add_subplot(2, 2, 4, projection='polar')
    bars = ax_polar.bar(theta, radii, width=np.pi/6, alpha=0.7, color='orange')
    ax_polar.set_title('Directional Displacement Rose Diagram')
    
    plt.tight_layout()
    
    base_path = os.path.join(output_dir, f"{filename}_displacement_analysis_slice{slice_idx}")
    save_plot(fig, base_path, save_formats)
    
    return base_path + '.png'

def plot_streamlines(flow_field, fixed_data, slice_idx, output_dir, filename, save_formats):
    """流线可视化"""
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    fig.suptitle(f'Deformation Streamlines - {filename}\nSlice {slice_idx}', 
                 fontsize=16, fontweight='bold')
    
    # 提取2D流场
    u = flow_field[:, :, slice_idx, 0]
    v = flow_field[:, :, slice_idx, 1]
    
    # 创建网格
    y, x = np.mgrid[0:u.shape[0], 0:u.shape[1]]
    
    # 左侧：在参考图像上显示流线
    ax1.imshow(fixed_data[:, :, slice_idx], cmap='gray', alpha=0.8)
    strm = ax1.streamplot(x, y, u, v, color=magnitude, cmap='viridis', 
                         linewidth=1.5, arrowsize=1.5, density=2)
    ax1.set_title('Streamlines on Reference Image')
    ax1.axis('off')
    plt.colorbar(strm.lines, ax=ax1, fraction=0.046)
    
    # 右侧：纯流线图
    magnitude = np.sqrt(u**2 + v**2)
    strm2 = ax2.streamplot(x, y, u, v, color=magnitude, cmap='plasma',
                          linewidth=2, arrowsize=2, density=2.5)
    ax2.set_title('Deformation Streamlines')
    ax2.axis('off')
    plt.colorbar(strm2.lines, ax=ax2, fraction=0.046)
    
    plt.tight_layout()
    
    base_path = os.path.join(output_dir, f"{filename}_streamlines_slice{slice_idx}")
    save_plot(fig, base_path, save_formats)
    
    return base_path + '.png'

def plot_multiplanar_view(flow_field, fixed_data, output_dir, filename, save_formats):
    """多平面可视化"""
    
    fig = plt.figure(figsize=(18, 12))
    gs = gridspec.GridSpec(3, 3, figure=fig)
    fig.suptitle(f'Multiplanar Deformation View - {filename}', 
                 fontsize=16, fontweight='bold')
    
    # 选择三个正交平面的中心切片
    slice_x = flow_field.shape[0] // 2
    slice_y = flow_field.shape[1] // 2  
    slice_z = flow_field.shape[2] // 2
    
    # 轴向面 (Axial - XY平面)
    ax1 = fig.add_subplot(gs[0, 0])
    magnitude_axial = np.sqrt(flow_field[slice_x, :, :, 1]**2 + flow_field[slice_x, :, :, 2]**2)
    im1 = ax1.imshow(magnitude_axial.T, cmap='viridis', origin='lower')
    ax1.set_title(f'Axial Plane (X={slice_x})')
    ax1.set_xlabel('Y')
    ax1.set_ylabel('Z')
    plt.colorbar(im1, ax=ax1, fraction=0.046)
    
    # 矢状面 (Sagittal - YZ平面)  
    ax2 = fig.add_subplot(gs[0, 1])
    magnitude_sagittal = np.sqrt(flow_field[:, slice_y, :, 0]**2 + flow_field[:, slice_y, :, 2]**2)
    im2 = ax2.imshow(magnitude_sagittal, cmap='viridis')
    ax2.set_title(f'Sagittal Plane (Y={slice_y})')
    ax2.set_xlabel('Z')
    ax2.set_ylabel('X')
    plt.colorbar(im2, ax=ax2, fraction=0.046)
    
    # 冠状面 (Coronal - XZ平面)
    ax3 = fig.add_subplot(gs[0, 2])
    magnitude_coronal = np.sqrt(flow_field[:, :, slice_z, 0]**2 + flow_field[:, :, slice_z, 1]**2)
    im3 = ax3.imshow(magnitude_coronal, cmap='viridis')
    ax3.set_title(f'Coronal Plane (Z={slice_z})')
    ax3.set_xlabel('X')
    ax3.set_ylabel('Y')
    plt.colorbar(im3, ax=ax3, fraction=0.046)
    
    # 3D散点图显示位移分布
    ax4 = fig.add_subplot(gs[1, :], projection='3d')
    
    # 下采样用于3D显示
    skip = 8
    x, y, z = np.mgrid[0:flow_field.shape[0]:skip, 
                      0:flow_field.shape[1]:skip, 
                      0:flow_field.shape[2]:skip]
    
    u = flow_field[::skip, ::skip, ::skip, 0]
    v = flow_field[::skip, ::skip, ::skip, 1]  
    w = flow_field[::skip, ::skip, ::skip, 2]
    mag = np.sqrt(u**2 + v**2 + w**2)
    
    scatter = ax4.scatter(x.flatten(), y.flatten(), z.flatten(), 
                         c=mag.flatten(), cmap='hot', alpha=0.6, s=10)
    ax4.set_xlabel('X')
    ax4.set_ylabel('Y')
    ax4.set_zlabel('Z')
    ax4.set_title('3D Displacement Distribution')
    plt.colorbar(scatter, ax=ax4, fraction=0.046)
    
    # 统计摘要
    ax5 = fig.add_subplot(gs[2, :])
    ax5.axis('off')
    
    overall_magnitude = np.sqrt(np.sum(flow_field**2, axis=3))
    stats_text = f"""Overall Deformation Statistics:
Mean Displacement: {overall_magnitude.mean():.4f} ± {overall_magnitude.std():.4f}
Max Displacement: {overall_magnitude.max():.4f}
95th Percentile: {np.percentile(overall_magnitude, 95):.4f}

Plane-specific Averages:
Axial (XY): {magnitude_axial.mean():.4f}
Sagittal (YZ): {magnitude_sagittal.mean():.4f}
Coronal (XZ): {magnitude_coronal.mean():.4f}

Volume Coverage:
Total voxels: {np.prod(flow_field.shape[:3]):,}
Moving voxels (>0.1): {np.sum(overall_magnitude > 0.1):,} ({np.sum(overall_magnitude > 0.1)/np.prod(flow_field.shape[:3])*100:.1f}%)"""
    
    ax5.text(0.05, 0.95, stats_text, transform=ax5.transAxes, fontsize=10,
             verticalalignment='top', bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
    
    plt.tight_layout()
    
    base_path = os.path.join(output_dir, f"{filename}_multiplanar_view")
    save_plot(fig, base_path, save_formats)
    
    return base_path + '.png'

def save_plot(fig, base_path, formats):
    """保存图片到多种格式"""
    for fmt in formats:
        path = f"{base_path}.{fmt}"
        fig.savefig(path, dpi=300, bbox_inches='tight', format=fmt)
        print(f"  💾 保存: {path}")
    plt.close(fig)

# 使用示例
if __name__ == "__main__":
    # 示例用法
    flow_field_path = "/media/dell/T7 Shield/nnunet/AllData/HK/finished/precontrast/dicom_to_nii/AD5737817.nii.gz"
    fixed_image_path = "/media/dell/T7 Shield/nnunet/AllData/HK/finished/precontrast/mask/peizhun/livertumor/AD5737817.nii_warped_moving.nii.gz" 
    output_dir = "/media/dell/T7 Shield/nnunet/AllData/HK/flow"
    
    # 生成所有可视化
    results = comprehensive_deformation_visualization(
        flow_field_path=flow_field_path,
        fixed_image_path=fixed_image_path, 
        output_dir=output_dir,
        slice_idx=50,  # 指定切片或自动选择
        vector_scale=40,
        density=6,
        save_formats=['png', 'pdf']
    )
    
    print("🎨 生成的可视化文件:")
    for name, path in results.items():
        if path:
            print(f"  {name}: {path}")