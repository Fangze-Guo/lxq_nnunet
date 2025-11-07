import SimpleITK as sitk
import os
import glob

# 输入输出路径
input_dir = "/media/dell/T7 Shield/nnunet/AllData/GDPH_118/LiverTumorLabels_160/C_L/spleen_liver_mask_pred"
output_dir = "/media/dell/T7 Shield/nnunet/AllData/GDPH_118/LiverTumorLabels_160/C_L/livertumor"

# 创建输出目录
os.makedirs(output_dir, exist_ok=True)

# 获取所有.nii.gz文件
nii_files = glob.glob(os.path.join(input_dir, "*.nii.gz"))

print(f"找到 {len(nii_files)} 个NIfTI文件")

for input_path in nii_files:
    # 构建输出文件名
    filename = os.path.basename(input_path)
    output_filename = filename.replace(".nii.gz", "_label15.nii.gz")
    output_path = os.path.join(output_dir, output_filename)
    
    try:
        # 读取多标签图像
        print(f"处理: {filename}")
        image = sitk.ReadImage(input_path)
        
        # 提取label 15（值为15的像素）
        label_15_mask = sitk.BinaryThreshold(image, lowerThreshold=15, upperThreshold=15)
        
        # 将提取的mask保存为二值图像（0和1）
        label_15_binary = sitk.Cast(label_15_mask, sitk.sitkUInt8)
        
        # 保存结果
        sitk.WriteImage(label_15_binary, output_path)
        print(f"✓ 成功保存: {output_filename}")
        
    except Exception as e:
        print(f"✗ 处理失败 {filename}: {e}")

print(f"\n处理完成！共处理 {len(nii_files)} 个文件")
print(f"输出目录: {output_dir}")