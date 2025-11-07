import os
import numpy as np
import nibabel as nib
import pandas as pd
from pathlib import Path
import logging
from tqdm import tqdm

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def count_nonzero_voxels(nifti_file):
    """统计nii.gz文件中的非零体素个数"""
    try:
        # 加载NIfTI文件
        img = nib.load(nifti_file)
        data = img.get_fdata()
        
        # 计算非零体素个数
        nonzero_count = np.count_nonzero(data)
        total_voxels = data.size
        
        # 计算零值体素个数和比例
        zero_count = total_voxels - nonzero_count
        nonzero_ratio = (nonzero_count / total_voxels) * 100 if total_voxels > 0 else 0
        
        # 获取数值范围
        min_value = float(np.min(data))
        max_value = float(np.max(data))
        
        # 获取非零值的统计
        nonzero_data = data[data != 0]
        if len(nonzero_data) > 0:
            nonzero_min = float(np.min(nonzero_data))
            nonzero_max = float(np.max(nonzero_data))
            nonzero_mean = float(np.mean(nonzero_data))
            nonzero_std = float(np.std(nonzero_data))
        else:
            nonzero_min = 0
            nonzero_max = 0
            nonzero_mean = 0
            nonzero_std = 0
        
        return {
            'filename': nifti_file.name,
            'file_path': str(nifti_file),
            'total_voxels': total_voxels,
            'nonzero_voxels': nonzero_count,
            'zero_voxels': zero_count,
            'nonzero_ratio_percent': round(nonzero_ratio, 2),
            'data_shape': str(data.shape),
            'data_type': str(data.dtype),
            'min_value': min_value,
            'max_value': max_value,
            'nonzero_min': nonzero_min,
            'nonzero_max': nonzero_max,
            'nonzero_mean': nonzero_mean,
            'nonzero_std': nonzero_std
        }
        
    except Exception as e:
        logger.error(f"处理文件 {nifti_file.name} 时出错: {str(e)}")
        return {
            'filename': nifti_file.name,
            'file_path': str(nifti_file),
            'total_voxels': 0,
            'nonzero_voxels': 0,
            'zero_voxels': 0,
            'nonzero_ratio_percent': 0,
            'data_shape': 'Error',
            'data_type': 'Error',
            'min_value': 0,
            'max_value': 0,
            'nonzero_min': 0,
            'nonzero_max': 0,
            'nonzero_mean': 0,
            'nonzero_std': 0,
            'error_message': str(e)
        }

def export_nonzero_stats_to_excel(nifti_dir, output_excel_path=None):
    """
    导出所有nii.gz文件的非零体素统计到Excel表格
    
    Args:
        nifti_dir: 包含nii.gz文件的目录路径
        output_excel_path: 输出Excel文件路径，如果为None则自动生成
    """
    nifti_dir = Path(nifti_dir)
    
    # 如果未指定输出路径，自动生成
    if output_excel_path is None:
        output_excel_path = nifti_dir / "nonzero_voxel_statistics.xlsx"
    else:
        output_excel_path = Path(output_excel_path)
    
    # 确保输出目录存在
    output_excel_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 查找所有nii.gz文件
    nifti_files = list(nifti_dir.glob("*.nii.gz"))
    
    if not nifti_files:
        logger.warning(f"在 {nifti_dir} 中未找到任何.nii.gz文件")
        return False
    
    logger.info(f"找到 {len(nifti_files)} 个nii.gz文件")
    
    # 收集所有文件的统计信息
    all_stats = []
    
    print("正在统计非零体素个数...")
    for nifti_file in tqdm(nifti_files, desc="处理文件"):
        stats = count_nonzero_voxels(nifti_file)
        all_stats.append(stats)
    
    # 创建DataFrame
    df = pd.DataFrame(all_stats)
    
    # 重新排列列的顺序，让重要信息在前面
    column_order = [
        'filename', 
        'nonzero_voxels', 
        'total_voxels', 
        'zero_voxels', 
        'nonzero_ratio_percent',
        'data_shape',
        'data_type',
        'min_value',
        'max_value',
        'nonzero_min',
        'nonzero_max',
        'nonzero_mean',
        'nonzero_std',
        'file_path'
    ]
    
    # 如果包含错误信息，也添加到列中
    if 'error_message' in df.columns:
        column_order.append('error_message')
    
    # 重新排列列顺序
    df = df.reindex(columns=column_order)
    
    # 创建Excel写入器
    with pd.ExcelWriter(output_excel_path, engine='openpyxl') as writer:
        # 工作表1: 详细统计
        df.to_excel(writer, sheet_name='详细统计', index=False)
        
        # 工作表2: 汇总统计
        summary_data = {
            '统计项目': [
                '文件总数',
                '总非零体素个数',
                '平均非零体素个数',
                '非零体素个数最大值',
                '非零体素个数最小值',
                '平均非零比例(%)',
                '非零比例最大值(%)',
                '非零比例最小值(%)'
            ],
            '数值': [
                len(df),
                df['nonzero_voxels'].sum(),
                df['nonzero_voxels'].mean(),
                df['nonzero_voxels'].max(),
                df['nonzero_voxels'].min(),
                df['nonzero_ratio_percent'].mean(),
                df['nonzero_ratio_percent'].max(),
                df['nonzero_ratio_percent'].min()
            ]
        }
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='汇总统计', index=False)
        
        # 工作表3: 按非零体素个数排序
        sorted_df = df.sort_values('nonzero_voxels', ascending=False)
        sorted_df.to_excel(writer, sheet_name='按非零个数排序', index=False)
        
        # 工作表4: 文件列表（简化版）
        simple_df = df[['filename', 'nonzero_voxels', 'total_voxels', 'nonzero_ratio_percent']].copy()
        simple_df.to_excel(writer, sheet_name='文件列表', index=False)
    
    logger.info(f"Excel文件已保存: {output_excel_path}")
    
    # 打印简要统计信息
    print("\n" + "="*60)
    print("非零体素统计摘要:")
    print(f"文件总数: {len(df)}")
    print(f"非零体素总数: {df['nonzero_voxels'].sum():,}")
    print(f"平均非零体素个数: {df['nonzero_voxels'].mean():.0f}")
    print(f"非零体素个数范围: {df['nonzero_voxels'].min():,} - {df['nonzero_voxels'].max():,}")
    print(f"平均非零比例: {df['nonzero_ratio_percent'].mean():.2f}%")
    print(f"非零比例范围: {df['nonzero_ratio_percent'].min():.2f}% - {df['nonzero_ratio_percent'].max():.2f}%")
    
    return True

def quick_nonzero_summary(nifti_dir):
    """快速显示非零体素统计摘要"""
    nifti_dir = Path(nifti_dir)
    nifti_files = list(nifti_dir.glob("*.nii.gz"))
    
    if not nifti_files:
        print(f"在 {nifti_dir} 中未找到任何.nii.gz文件")
        return
    
    print(f"找到 {len(nifti_files)} 个nii.gz文件")
    print("="*80)
    
    nonzero_counts = []
    
    for nifti_file in nifti_files[:10]:  # 只显示前10个文件
        try:
            img = nib.load(nifti_file)
            data = img.get_fdata()
            nonzero_count = np.count_nonzero(data)
            total_voxels = data.size
            ratio = (nonzero_count / total_voxels) * 100
            
            nonzero_counts.append(nonzero_count)
            
            print(f"{nifti_file.name}")
            print(f"  非零体素: {nonzero_count:,} / {total_voxels:,} ({ratio:.2f}%)")
            print(f"  数据形状: {data.shape}")
            print()
            
        except Exception as e:
            print(f"处理文件 {nifti_file.name} 时出错: {str(e)}")
            print()
    
    if nonzero_counts:
        print("前10个文件统计:")
        print(f"  平均非零体素个数: {np.mean(nonzero_counts):.0f}")
        print(f"  非零体素个数范围: {np.min(nonzero_counts):,} - {np.max(nonzero_counts):,}")

def main():
    """主函数"""
    # 设置路径
    nifti_dir = "/media/dell/T7 Shield/nnunet/AllData/ZJYY/15例_pre/ZJYY_93/pre_livertumor_93"
    output_excel = "/media/dell/T7 Shield/nnunet/AllData/ZJYY/15例_pre/ZJYY_93/nonzero_statistics.xlsx"
    
    print("开始统计nii.gz文件的非零体素个数...")
    print(f"输入目录: {nifti_dir}")
    print(f"输出文件: {output_excel}")
    print("=" * 60)
    
    # 首先显示快速预览
    print("快速预览前10个文件:")
    quick_nonzero_summary(nifti_dir)
    
    # 执行完整导出
    success = export_nonzero_stats_to_excel(nifti_dir, output_excel)
    
    if success:
        print(f"\n导出完成！Excel文件已保存到: {output_excel}")
        print("\nExcel文件包含以下工作表:")
        print("1. '详细统计' - 所有文件的完整统计信息")
        print("2. '汇总统计' - 总体统计摘要")
        print("3. '按非零个数排序' - 按非零体素个数从高到低排序")
        print("4. '文件列表' - 简化的文件列表")
    else:
        print("\n导出失败，请检查目录路径和文件格式")

if __name__ == "__main__":
    main()