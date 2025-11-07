import SimpleITK as sitk
import os

def dicom_to_nii(dicom_folder, output_path):
    """
    将DICOM序列转换为NII.GZ格式
    
    参数:
    dicom_folder: DICOM文件夹路径
    output_path: 输出NII.GZ文件路径
    """
    # 读取DICOM序列
    reader = sitk.ImageSeriesReader()
    
    # 获取DICOM序列ID
    dicom_names = reader.GetGDCMSeriesFileNames(dicom_folder)
    reader.SetFileNames(dicom_names)
    
    # 读取图像
    image = reader.Execute()
    
    # 保存为NII.GZ
    sitk.WriteImage(image, output_path)
    print(f"转换完成: {output_path}")

# 使用示例
dicom_folder = "/media/dell/T7 Shield/nnunet/AllData/PKUShZh/重新配置/1489231/009_t1_vibe_dixon_tra_p4_bh_pre_W"
output_file = "/media/dell/T7 Shield/nnunet/AllData/PKUShZh/重新配置/1489231/1489231.nii.gz"

dicom_to_nii(dicom_folder, output_file)