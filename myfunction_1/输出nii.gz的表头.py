import nibabel as nib
import numpy as np

# 文件路径
file1_path = "/media/dell/T7 Shield/nnunet/AllData/HK/finished/precontrast/dicom_to_nii/AD5737817.nii.gz"
file2_path = "/media/dell/T7 Shield/nnunet/AllData/HK/finished/HBP/dicom_to_nii_gandan/AD5737817.nii.gz"

# 读取图像
img1 = nib.load(file1_path)
img2 = nib.load(file2_path)

# 获取头信息
header1 = img1.header
header2 = img2.header

print("=" * 60)
print("图像1 (Precontrast) 信息:")
print("=" * 60)
print(f"数据形状: {img1.shape}")
print(f"体素尺寸: {header1.get_zooms()}")
print(f"数据类型: {header1.get_data_dtype()}")
print(f"qform_code: {header1['qform_code']}")
print(f"sform_code: {header1['sform_code']}")

print("\n仿射矩阵 - 图像1:")
print(img1.affine)

print("\n" + "=" * 60)
print("图像2 (HBP) 信息:")
print("=" * 60)
print(f"数据形状: {img2.shape}")
print(f"体素尺寸: {header2.get_zooms()}")
print(f"数据类型: {header2.get_data_dtype()}")
print(f"qform_code: {header2['qform_code']}")
print(f"sform_code: {header2['sform_code']}")

print("\n仿射矩阵 - 图像2:")
print(img2.affine)

print("\n" + "=" * 60)
print("关键差异比较:")
print("=" * 60)

# 比较关键参数
shape_diff = np.array(img1.shape) - np.array(img2.shape)
voxel_diff = np.array(header1.get_zooms()) - np.array(header2.get_zooms())
affine_diff = np.abs(img1.affine - img2.affine)

print(f"形状差异: {shape_diff}")
print(f"体素尺寸差异: {voxel_diff}")
print(f"仿射矩阵最大差异: {np.max(affine_diff):.6f}")

# 检查方向标识符
def get_orientation(affine):
    """从仿射矩阵获取方向"""
    orient = ''
    for i in range(3):
        if np.argmax(np.abs(affine[:3, i])) == 0:
            orient += 'R' if affine[0, i] > 0 else 'L'
        elif np.argmax(np.abs(affine[:3, i])) == 1:
            orient += 'A' if affine[1, i] > 0 else 'P'
        else:
            orient += 'S' if affine[2, i] > 0 else 'I'
    return orient

orient1 = get_orientation(img1.affine)
orient2 = get_orientation(img2.affine)

print(f"图像1方向: {orient1}")
print(f"图像2方向: {orient2}")
print(f"方向是否一致: {orient1 == orient2}")

# 检查物理空间原点位置
origin1 = img1.affine[:3, 3]
origin2 = img2.affine[:3, 3]
origin_diff = np.abs(origin1 - origin2)

print(f"图像1原点: {origin1}")
print(f"图像2原点: {origin2}")
print(f"原点差异: {origin_diff}")

# 检查qform/sform代码一致性
print(f"qform_code一致: {header1['qform_code'] == header2['qform_code']}")
print(f"sform_code一致: {header1['sform_code'] == header2['sform_code']}")