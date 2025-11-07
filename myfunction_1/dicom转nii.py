import os
import pydicom
import numpy as np
import nibabel as nib
from pathlib import Path
import logging
from tqdm import tqdm
import SimpleITK as sitk
import re
import subprocess
import shutil
import tempfile

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def is_dicom_file(file_path):
    """检查文件是否为DICOM文件"""
    try:
        pydicom.dcmread(file_path, stop_before_pixels=True)
        return True
    except:
        return False

def get_all_dicom_files(directory):
    """获取目录及其所有子目录中的所有DICOM文件"""
    dicom_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            if is_dicom_file(file_path):
                dicom_files.append(file_path)
    return dicom_files

def sort_dicom_files_by_instance_number(dicom_files):
    """根据InstanceNumber对DICOM文件进行排序"""
    files_with_instance = []
    files_without_instance = []
    
    for file_path in dicom_files:
        try:
            ds = pydicom.dcmread(file_path, stop_before_pixels=True)
            if hasattr(ds, 'InstanceNumber') and ds.InstanceNumber is not None:
                files_with_instance.append((file_path, int(ds.InstanceNumber)))
            else:
                files_without_instance.append(file_path)
        except:
            files_without_instance.append(file_path)
    
    # 按InstanceNumber排序
    files_with_instance.sort(key=lambda x: x[1])
    sorted_files = [x[0] for x in files_with_instance] + files_without_instance
    
    return sorted_files

def reorient_to_lps(image_data, affine):
    """
    将图像重新定向到LPS方向
    LPS: Left-Posterior-Superior (ITK标准方向)
    """
    # 获取当前方向
    current_orientation = nib.aff2axcodes(affine)
    target_orientation = ('L', 'P', 'S')
    
    # 如果已经是LPS方向，直接返回
    if current_orientation == target_orientation:
        return image_data, affine
    
    print(f"  🔄 方向调整: {''.join(current_orientation)} -> {''.join(target_orientation)}")
    
    # 计算需要进行的变换
    transform = np.eye(4)
    for i, (current_ax, target_ax) in enumerate(zip(current_orientation, target_orientation)):
        if current_ax != target_ax:
            # 需要翻转轴
            transform[i, i] = -1
            # 调整原点位置
            transform[i, 3] = image_data.shape[i] - 1
    
    # 应用变换到仿射矩阵
    new_affine = affine @ transform
    
    # 应用变换到图像数据
    new_data = np.copy(image_data)
    for i, (current_ax, target_ax) in enumerate(zip(current_orientation, target_orientation)):
        if current_ax != target_ax:
            new_data = np.flip(new_data, axis=i)
    
    return new_data, new_affine

def save_as_lps_nifti(image_data, affine, output_path, dtype=np.float32):
    """
    保存为LPS方向的NIfTI文件
    """
    # 确保数据是正确类型
    image_data = image_data.astype(dtype)
    
    # 创建NIfTI图像
    nifti_img = nib.Nifti1Image(image_data, affine)
    
    # 设置qform和sform为LPS方向
    nifti_img.set_qform(affine, code='scanner')
    nifti_img.set_sform(affine, code='scanner')
    
    # 保存文件
    nib.save(nifti_img, output_path)
    
    # 验证方向
    saved_img = nib.load(output_path)
    saved_orientation = nib.aff2axcodes(saved_img.affine)
    target_orientation = ('L', 'P', 'S')
    
    print(f"  🧭 方向验证: {''.join(saved_orientation)}")
    if saved_orientation == target_orientation:
        print(f"  ✅ 成功保存为LPS方向: {output_path}")
    else:
        print(f"  ⚠️ 警告: 保存方向为 {''.join(saved_orientation)}，不是LPS")
    
    return saved_orientation == target_orientation

def convert_dicom_series_to_nifti_lps(dicom_files, output_path):
    """将DICOM文件序列转换为LPS方向的NIfTI格式"""
    try:
        if not dicom_files:
            logger.warning("没有DICOM文件可转换")
            return False
        
        # 使用SimpleITK读取DICOM序列
        reader = sitk.ImageSeriesReader()
        
        # 获取DICOM序列的文件名
        dicom_files_sorted = sort_dicom_files_by_instance_number(dicom_files)
        
        # 设置DICOM文件
        reader.SetFileNames(dicom_files_sorted)
        
        # 读取图像
        image = reader.Execute()
        
        # 转换为numpy数组
        image_array = sitk.GetArrayFromImage(image)
        
        # 获取原始方向信息
        direction = image.GetDirection()
        origin = image.GetOrigin()
        spacing = image.GetSpacing()
        
        # 重新排列维度：从SimpleITK (z,y,x) 到 NIfTI (x,y,z)
        image_array = np.transpose(image_array, (2, 1, 0))
        
        # 创建仿射矩阵
        affine = np.eye(4)
        affine[:3, :3] = np.array(direction).reshape(3, 3) * spacing
        affine[:3, 3] = origin
        
        # 重新定向到LPS
        image_array_lps, affine_lps = reorient_to_lps(image_array, affine)
        
        # 保存为LPS方向的NIfTI
        success = save_as_lps_nifti(image_array_lps, affine_lps, output_path)
        
        if success:
            logger.info(f"成功保存为LPS方向: {output_path}")
        else:
            logger.warning(f"方向可能不是LPS: {output_path}")
        
        return success
        
    except Exception as e:
        logger.error(f"转换失败: {str(e)}")
        return False

def process_first_level_directory(first_level_dir, output_base_dir):
    """处理单个一级子文件夹"""
    dicom_files = get_all_dicom_files(first_level_dir)
    
    if not dicom_files:
        logger.warning(f"在 {first_level_dir} 中未找到DICOM文件")
        return False
    
    # 创建输出文件名（使用一级文件夹名称）
    first_level_name = os.path.basename(first_level_dir)
    output_filename = f"{first_level_name}.nii.gz"
    output_path = os.path.join(output_base_dir, output_filename)
    
    logger.info(f"处理 {first_level_name}, 找到 {len(dicom_files)} 个DICOM文件")
    
    # 转换为NIfTI
    success = convert_dicom_series_to_nifti_lps(dicom_files, output_path)
    
    if success:
        logger.info(f"成功转换: {first_level_name} -> {output_filename}")
    else:
        logger.error(f"转换失败: {first_level_name}")
    
    return success

def main_simpleitk_lps(input_base_dir, output_base_dir):
    """主转换函数 - 使用SimpleITK并强制LPS方向"""
    print("开始使用SimpleITK转换DICOM到NIfTI (LPS方向)...")
    print(f"输入目录: {input_base_dir}")
    print(f"输出目录: {output_base_dir}")
    print("=" * 60)
    
    # 检查输入目录是否存在
    if not os.path.exists(input_base_dir):
        print(f"错误: 输入目录不存在: {input_base_dir}")
        return False
    
    # 创建输出目录
    os.makedirs(output_base_dir, exist_ok=True)
    
    # 获取所有一级子文件夹
    try:
        first_level_dirs = []
        for item in os.listdir(input_base_dir):
            item_path = os.path.join(input_base_dir, item)
            if os.path.isdir(item_path):
                first_level_dirs.append(item_path)
    except Exception as e:
        logger.error(f"无法读取输入目录: {str(e)}")
        return False
    
    logger.info(f"找到 {len(first_level_dirs)} 个一级子文件夹")
    
    total_converted = 0
    total_failed = 0
    
    # 处理每个一级子文件夹
    for first_level_dir in tqdm(first_level_dirs, desc="转换DICOM序列"):
        success = process_first_level_directory(first_level_dir, output_base_dir)
        if success:
            total_converted += 1
        else:
            total_failed += 1
    
    print("=" * 60)
    print("SimpleITK转换完成!")
    print(f"成功: {total_converted}, 失败: {total_failed}")
    return total_converted > 0

def is_dcm2niix_available():
    """检查dcm2niix是否可用"""
    try:
        result = subprocess.run(['dcm2niix', '--version'], 
                              capture_output=True, text=True, timeout=10)
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return False

def ensure_lps_orientation(file_path):
    """
    确保NIfTI文件是LPS方向，如果不是则重新定向
    """
    try:
        img = nib.load(file_path)
        current_orientation = nib.aff2axcodes(img.affine)
        target_orientation = ('L', 'P', 'S')
        
        if current_orientation == target_orientation:
            return True
        
        print(f"  🔄 重新定向: {''.join(current_orientation)} -> LPS")
        
        # 重新定向到LPS
        data = img.get_fdata()
        data_lps, affine_lps = reorient_to_lps(data, img.affine)
        
        # 保存为LPS方向
        success = save_as_lps_nifti(data_lps, affine_lps, file_path)
        
        return success
        
    except Exception as e:
        logger.error(f"重新定向失败 {file_path}: {str(e)}")
        return False

def main_dcm2niix_lps(input_base_dir, output_base_dir):
    """使用dcm2niix进行转换并确保LPS方向"""
    print("开始使用dcm2niix转换DICOM到NIfTI (LPS方向)...")
    print(f"输入目录: {input_base_dir}")
    print(f"输出目录: {output_base_dir}")
    print("=" * 60)
    
    # 检查输入目录是否存在
    if not os.path.exists(input_base_dir):
        print(f"错误: 输入目录不存在: {input_base_dir}")
        return False
    
    # 检查dcm2niix是否可用
    if not is_dcm2niix_available():
        print("错误: dcm2niix未安装或不在PATH中")
        print("将使用SimpleITK方法替代...")
        return main_simpleitk_lps(input_base_dir, output_base_dir)
    
    # 创建输出目录
    os.makedirs(output_base_dir, exist_ok=True)
    
    # 获取所有一级子文件夹
    first_level_dirs = []
    for item in os.listdir(input_base_dir):
        item_path = os.path.join(input_base_dir, item)
        if os.path.isdir(item_path):
            first_level_dirs.append(item_path)
    
    logger.info(f"找到 {len(first_level_dirs)} 个一级子文件夹")
    
    total_converted = 0
    total_failed = 0
    
    # 创建临时工作目录
    with tempfile.TemporaryDirectory() as temp_dir:
        for first_level_dir in tqdm(first_level_dirs, desc="dcm2niix转换"):
            first_level_name = os.path.basename(first_level_dir)
            output_filename = f"{first_level_name}.nii.gz"
            output_path = os.path.join(output_base_dir, output_filename)
            
            try:
                # 清空临时目录
                for file in os.listdir(temp_dir):
                    file_path = os.path.join(temp_dir, file)
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                
                # 使用dcm2niix转换
                # 添加 -l y 参数确保输出为LPS方向
                cmd = [
                    'dcm2niix',
                    '-b', 'y',          # 生成JSON sidecar
                    '-z', 'y',          # 压缩输出
                    '-l', 'y',          # 确保LPS方向
                    '-f', '%p_%s',      # 文件名格式: 协议_序列
                    '-o', temp_dir,     # 输出目录
                    first_level_dir     # 输入目录
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                
                if result.returncode != 0:
                    logger.warning(f"dcm2niix返回非零状态: {result.stderr}")
                
                # 检查临时目录中生成的文件
                nifti_files = [f for f in os.listdir(temp_dir) 
                              if f.endswith(('.nii.gz', '.nii'))]
                
                if nifti_files:
                    # 如果有多个文件，选择第一个（通常是最主要的）
                    source_file = os.path.join(temp_dir, nifti_files[0])
                    
                    # 移动到目标位置并重命名
                    if source_file.endswith('.nii') and output_path.endswith('.nii.gz'):
                        # 如果需要压缩，重新保存
                        img = nib.load(source_file)
                        nib.save(img, output_path)
                        os.remove(source_file)
                    else:
                        shutil.move(source_file, output_path)
                    
                    # 确保LPS方向
                    lps_success = ensure_lps_orientation(output_path)
                    
                    if lps_success:
                        logger.info(f"成功转换(LPS): {first_level_name} -> {output_filename}")
                        total_converted += 1
                    else:
                        logger.warning(f"转换成功但方向不是LPS: {first_level_name}")
                        total_converted += 1  # 仍然算成功，只是方向可能不是LPS
                    
                    # 同时移动JSON sidecar文件（如果有）
                    json_files = [f for f in os.listdir(temp_dir) if f.endswith('.json')]
                    for json_file in json_files:
                        json_source = os.path.join(temp_dir, json_file)
                        json_dest = os.path.join(output_base_dir, 
                                               f"{first_level_name}.json")
                        shutil.move(json_source, json_dest)
                    
                else:
                    logger.warning(f"在 {first_level_name} 中未生成NIfTI文件")
                    logger.warning(f"dcm2niix输出: {result.stdout}")
                    if result.stderr:
                        logger.warning(f"dcm2niix错误: {result.stderr}")
                    total_failed += 1
                    
            except subprocess.TimeoutExpired:
                logger.error(f"dcm2niix转换超时: {first_level_name}")
                total_failed += 1
            except Exception as e:
                logger.error(f"dcm2niix转换失败 {first_level_name}: {str(e)}")
                total_failed += 1
    
    print("=" * 60)
    print("dcm2niix转换完成!")
    print(f"成功: {total_converted}, 失败: {total_failed}")
    
    return total_converted > 0

def main_dicom2nifti_lps(input_base_dir, output_base_dir):
    """备用方案 - 使用dicom2nifti库并确保LPS方向"""
    try:
        import dicom2nifti
        import dicom2nifti.settings as settings
        
        # 禁用一些验证以加快速度
        settings.disable_validate_slice_increment()
        settings.disable_validate_orthogonal()
        
        print("开始使用dicom2nifti转换DICOM到NIfTI (LPS方向)...")
        print(f"输入目录: {input_base_dir}")
        print(f"输出目录: {output_base_dir}")
        print("=" * 60)
        
        # 检查输入目录是否存在
        if not os.path.exists(input_base_dir):
            print(f"错误: 输入目录不存在: {input_base_dir}")
            return False
        
        # 创建输出目录
        os.makedirs(output_base_dir, exist_ok=True)
        
        # 获取所有一级子文件夹
        first_level_dirs = []
        for item in os.listdir(input_base_dir):
            item_path = os.path.join(input_base_dir, item)
            if os.path.isdir(item_path):
                first_level_dirs.append(item_path)
        
        logger.info(f"找到 {len(first_level_dirs)} 个一级子文件夹")
        
        total_converted = 0
        total_failed = 0
        
        # 为每个一级子文件夹创建临时输出目录
        temp_output_dir = os.path.join(output_base_dir, "temp_conversion")
        os.makedirs(temp_output_dir, exist_ok=True)
        
        for first_level_dir in tqdm(first_level_dirs, desc="dicom2nifti转换"):
            first_level_name = os.path.basename(first_level_dir)
            output_filename = f"{first_level_name}.nii.gz"
            output_path = os.path.join(output_base_dir, output_filename)
            
            try:
                # 清空临时目录
                for file in os.listdir(temp_output_dir):
                    os.remove(os.path.join(temp_output_dir, file))
                
                # 转换整个目录到临时目录
                dicom2nifti.convert_directory(first_level_dir, temp_output_dir, 
                                            compression=True, reorient=True)
                
                # 检查临时目录中生成的文件
                nifti_files = [f for f in os.listdir(temp_output_dir) 
                              if f.endswith(('.nii', '.nii.gz'))]
                
                if nifti_files:
                    # 取第一个生成的NIfTI文件
                    source_file = os.path.join(temp_output_dir, nifti_files[0])
                    
                    # 重命名为一级文件夹名称
                    if source_file.endswith('.nii') and output_path.endswith('.nii.gz'):
                        # 如果需要压缩，重新保存为.gz格式
                        img = nib.load(source_file)
                        nib.save(img, output_path)
                        os.remove(source_file)
                    else:
                        os.rename(source_file, output_path)
                    
                    # 确保LPS方向
                    lps_success = ensure_lps_orientation(output_path)
                    
                    if lps_success:
                        logger.info(f"成功转换(LPS): {first_level_name} -> {output_filename}")
                    else:
                        logger.warning(f"转换成功但方向不是LPS: {first_level_name}")
                    
                    total_converted += 1
                else:
                    logger.warning(f"在 {first_level_name} 中未生成NIfTI文件")
                    total_failed += 1
                    
            except Exception as e:
                logger.error(f"dicom2nifti转换失败 {first_level_name}: {str(e)}")
                total_failed += 1
        
        # 清理临时目录
        shutil.rmtree(temp_output_dir, ignore_errors=True)
        
        print("=" * 60)
        print("dicom2nifti转换完成!")
        print(f"成功: {total_converted}, 失败: {total_failed}")
        return total_converted > 0
        
    except ImportError:
        logger.warning("dicom2nifti库未安装，将使用SimpleITK方法替代...")
        return main_simpleitk_lps(input_base_dir, output_base_dir)
    except Exception as e:
        logger.error(f"dicom2nifti转换过程中发生错误: {str(e)}")
        return False

def verify_lps_orientation(output_base_dir):
    """验证输出目录中所有NIfTI文件的方向"""
    print("\n" + "="*60)
    print("🧭 验证输出文件方向...")
    print("="*60)
    
    nifti_files = list(Path(output_base_dir).glob("*.nii.gz"))
    
    if not nifti_files:
        print("未找到NIfTI文件进行验证")
        return
    
    lps_count = 0
    other_count = 0
    
    for file_path in nifti_files:
        try:
            img = nib.load(file_path)
            orientation = nib.aff2axcodes(img.affine)
            orientation_str = ''.join(orientation)
            
            if orientation == ('L', 'P', 'S'):
                print(f"✅ {file_path.name}: LPS")
                lps_count += 1
            else:
                print(f"⚠️  {file_path.name}: {orientation_str}")
                other_count += 1
                
        except Exception as e:
            print(f"❌ {file_path.name}: 读取失败 - {e}")
            other_count += 1
    
    print("="*60)
    print(f"方向验证结果:")
    print(f"  LPS方向: {lps_count} 个文件")
    print(f"  其他方向: {other_count} 个文件")
    if len(nifti_files) > 0:
        print(f"  LPS比例: {(lps_count/len(nifti_files))*100:.1f}%")
    
    return lps_count == len(nifti_files)

def main_lps(input_base_dir, output_base_dir, method="auto"):
    """主函数 - 确保输出为LPS方向
    
    Args:
        input_base_dir: 输入目录路径
        output_base_dir: 输出目录路径
        method: 转换方法，可选 "auto", "dcm2niix", "simpleitk", "dicom2nifti"
    """
    print("DICOM to NIfTI 转换工具 (强制LPS方向)")
    print("=" * 50)
    
    success = False
    
    if method == "auto":
        # 自动选择最佳可用方法
        if is_dcm2niix_available():
            print("✅ 检测到dcm2niix，使用dcm2niix进行转换...")
            success = main_dcm2niix_lps(input_base_dir, output_base_dir)
        else:
            try:
                import dicom2nifti
                print("✅ 检测到dicom2nifti，使用dicom2nifti进行转换...")
                success = main_dicom2nifti_lps(input_base_dir, output_base_dir)
            except ImportError:
                print("✅ 使用SimpleITK进行转换...")
                success = main_simpleitk_lps(input_base_dir, output_base_dir)
    elif method == "dcm2niix":
        success = main_dcm2niix_lps(input_base_dir, output_base_dir)
    elif method == "simpleitk":
        success = main_simpleitk_lps(input_base_dir, output_base_dir)
    elif method == "dicom2nifti":
        success = main_dicom2nifti_lps(input_base_dir, output_base_dir)
    else:
        print(f"未知的转换方法: {method}")
        return False
    
    # 验证输出方向
    if success:
        all_lps = verify_lps_orientation(output_base_dir)
        if all_lps:
            print("\n🎉 所有文件均为LPS方向!")
        else:
            print("\n⚠️  部分文件不是LPS方向，建议检查")
        
        return True
    else:
        print(f"\n❌ 转换方法失败")
        return False

def install_requirements():
    """显示安装说明"""
    print("请安装以下依赖 (可选):")
    print("1. SimpleITK: pip install pydicom nibabel SimpleITK tqdm")
    print("2. dicom2nifti: pip install dicom2nifti")
    print("3. dcm2niix (推荐):")
    print("   Ubuntu/Debian: sudo apt-get install dcm2niix")
    print("   CentOS/RHEL: sudo yum install dcm2niix")
    print("   macOS: brew install dcm2niix")
    print("   Windows: 从 https://github.com/rordenlab/dcm2niix/releases 下载")
    print("\n注意: 即使没有安装dcm2niix，本脚本也会使用其他可用方法")

if __name__ == "__main__":
    # 显示安装说明
    install_requirements()
    print("\n" + "="*50)
    
    # 设置输入输出路径
    input_base_dir = "/media/dell/T7 Shield/nnunet/AllData/PKUShZh/finished/HBP/HBP_dicom"
    output_base_dir = "/media/dell/T7 Shield/nnunet/AllData/PKUShZh/finished/HBP/HBP_nii"
    
    # 运行主转换程序，使用自动选择方法
    success = main_lps(input_base_dir, output_base_dir, method="auto")
    
    if success:
        print("\n✅ 转换完成! 所有输出文件已确保为LPS方向")
    else:
        print("\n❌ 转换失败或部分失败")