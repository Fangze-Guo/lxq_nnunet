import os
import SimpleITK as sitk
from glob import glob
from tqdm import tqdm

def convert_dicom_to_nifti(dicom_root, output_dir):
    """
    将三级目录结构的DICOM序列转换为独立的NIfTI文件
    目录结构: 主目录/患者ID/序列号/*.DCM
    """
    print("="*60)
    print(f"扫描目录: {dicom_root}")
    print(f"输出目录: {output_dir}")
    print("目录结构要求: 一级文件夹/二级子文件夹(患者ID)/三级子文件夹(序列号)/*.DCM")
    print("="*60)
    
    os.makedirs(output_dir, exist_ok=True)
    
    # 获取所有患者文件夹
    patient_dirs = sorted(glob(os.path.join(dicom_root, "*")))
    total_series = 0
    success_count = 0
    
    for patient_dir in patient_dirs:
        if not os.path.isdir(patient_dir):
            continue
            
        # 获取患者ID（二级文件夹名）
        patient_id = os.path.basename(patient_dir)
        
        # 获取所有序列文件夹
        series_dirs = sorted(glob(os.path.join(patient_dir, "*")))
        
        for series_dir in series_dirs:
            if not os.path.isdir(series_dir):
                continue
                
            total_series += 1
            series_name = os.path.basename(series_dir)
            output_filename = f"{patient_id}_{series_name}.nii.gz"
            output_path = os.path.join(output_dir, output_filename)
            
            print(f"Found DICOM series: {series_dir} -> {output_path}")
            
            try:
                # 读取DICOM序列
                reader = sitk.ImageSeriesReader()
                dicom_names = reader.GetGDCMSeriesFileNames(series_dir)
                reader.SetFileNames(dicom_names)
                image = reader.Execute()
                
                # 保存为NIfTI
                sitk.WriteImage(image, output_path)
                print(f"✅ {output_path}")
                success_count += 1
            except Exception as e:
                print(f"❌ 转换失败: {series_dir} - {str(e)}")
    
    print(f"\n🎉 转换完成! 成功: {success_count}/{total_series}")
    print(f"输出目录: {output_dir}")

if __name__ == "__main__":
    dicom_root = "/media/cqc/新加卷/my_data/HK/另外三个蒙片"
    output_dir = "/media/cqc/新加卷/my_data/HK/另外三个蒙片_nii"
    convert_dicom_to_nifti(dicom_root, output_dir)