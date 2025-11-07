import nibabel as nib
import numpy as np
import os

def remove_last_slices(nifti_file_path, num_slices_to_remove=7, output_path=None):
    """
    从NIfTI文件中删除最后几个切片
    
    参数:
    nifti_file_path: NIfTI文件路径
    num_slices_to_remove: 要删除的切片数量（默认为7）
    output_path: 输出文件路径（如果为None，则覆盖原文件）
    """
    
    # 加载NIfTI文件
    img = nib.load(nifti_file_path)
    data = img.get_fdata()
    affine = img.affine
    header = img.header
    
    print(f"原始图像形状: {data.shape}")
    print(f"原始数据类型: {data.dtype}")
    
    # 检查是否有足够的切片可以删除
    if data.ndim < 3:
        raise ValueError("图像维度不足，至少需要3D数据")
    
    if data.shape[2] <= num_slices_to_remove:
        raise ValueError(f"无法删除 {num_slices_to_remove} 个切片，图像只有 {data.shape[2]} 个切片")
    
    # 删除最后几个切片
    new_data = data[:, :, :-num_slices_to_remove]
    print(f"新图像形状: {new_data.shape}")
    
    # 创建新的NIfTI图像
    new_img = nib.Nifti1Image(new_data, affine, header)
    
    # 确定输出路径
    if output_path is None:
        output_path = nifti_file_path
    
    # 保存新的NIfTI文件
    nib.save(new_img, output_path)
    print(f"文件已保存: {output_path}")
    
    return new_data.shape

def main():
    # 设置文件路径
    input_file = "/media/dell/T7 Shield/nnunet/AllData/珠江医院/dicom_to_nii/4470492.nii.gz"
    
    # 检查文件是否存在
    if not os.path.exists(input_file):
        print(f"错误: 文件不存在: {input_file}")
        return
    
    try:
        # 删除最后7个切片
        new_shape = remove_last_slices(input_file, num_slices_to_remove=7)
        
        print(f"\n操作完成!")
        print(f"已从 {os.path.basename(input_file)} 中删除最后7个切片")
        print(f"新图像维度: {new_shape}")
        
    except Exception as e:
        print(f"处理过程中发生错误: {e}")

def batch_remove_slices(directory, file_patterns=None, num_slices_to_remove=7):
    """
    批量处理目录中的多个NIfTI文件
    
    参数:
    directory: 目录路径
    file_patterns: 文件模式列表（如 ['*.nii', '*.nii.gz']）
    num_slices_to_remove: 要删除的切片数量
    """
    if file_patterns is None:
        file_patterns = ['*.nii', '*.nii.gz']
    
    import glob
    
    # 获取所有匹配的文件
    nifti_files = []
    for pattern in file_patterns:
        nifti_files.extend(glob.glob(os.path.join(directory, pattern)))
    
    print(f"找到 {len(nifti_files)} 个NIfTI文件")
    
    success_count = 0
    for file_path in nifti_files:
        try:
            print(f"\n处理文件: {os.path.basename(file_path)}")
            remove_last_slices(file_path, num_slices_to_remove)
            success_count += 1
        except Exception as e:
            print(f"处理 {os.path.basename(file_path)} 失败: {e}")
    
    print(f"\n批量处理完成! 成功: {success_count}/{len(nifti_files)}")

if __name__ == "__main__":
    # 处理单个文件
    main()
    
    # 如果需要批量处理，取消下面的注释
    # directory = "/media/dell/T7 Shield/nnunet/AllData/珠江医院/dicom_to_nii/"
    # batch_remove_slices(directory, num_slices_to_remove=7)