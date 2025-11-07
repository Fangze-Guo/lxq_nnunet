import os
import nibabel as nib
import numpy as np
import pandas as pd

def check_ct_or_mri(nii_path, hu_threshold=500):
    """
    判断单个 .nii.gz 文件是 CT 还是 MRI
    :param nii_path: 文件路径
    :param hu_threshold: CT 的典型 HU 阈值（骨骼 > 300 HU）
    :return: "CT" 或 "MRI"
    """
    try:
        img = nib.load(nii_path)
        data = img.get_fdata()
        min_val, max_val = np.min(data), np.max(data)
        return "CT" if (min_val < -100 or max_val > hu_threshold) else "MRI"
    except Exception as e:
        return f"Error: {str(e)}"

def batch_check_nii_folder(folder_path, output_csv="DATASET/nnUNet_raw/dataset_type/result_train.csv"):
    """
    批量检查文件夹中所有 .nii.gz 文件
    :param folder_path: 文件夹路径
    :param output_csv: 输出 CSV 文件名
    """
    results = []
    for file in os.listdir(folder_path):
        if file.endswith(".nii.gz"):
            file_path = os.path.join(folder_path, file)
            modality = check_ct_or_mri(file_path)
            results.append({"File": file, "Modality": modality})
    
    # 保存为 CSV
    df = pd.DataFrame(results)
    df.to_csv(output_csv, index=False)
    print(f"结果已保存到 {output_csv}")
    return df

# 使用示例
if __name__ == "__main__":
    folder_path = r"DATASET/nnUNet_raw/Task001_example/imagesTr"  # 替换为你的文件夹路径
    result_df = batch_check_nii_folder(folder_path)
    print(result_df)