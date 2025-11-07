import SimpleITK as sitk

# SimpleITK 对方向矩阵的处理更宽松
image = sitk.ReadImage("/media/dell/T7 Shield/nnunet/AllData/PKUShZh/1489231.nii.gz")

# 保存为新的NIFTI文件
sitk.WriteImage(image, "/media/dell/T7 Shield/nnunet/AllData/PKUShZh/1489231_new.nii.gz")