import os
import numpy as np
import nibabel as nib
import pandas as pd
from glob import glob

def load_nifti_file(file_path):
    """加载NIfTI文件并返回数据数组"""
    img = nib.load(file_path)
    return img.get_fdata()

def calculate_dice(pred, truth):
    """计算Dice系数"""
    # 确保数据是二值化的（0和1）
    pred_binary = (pred > 0.5).astype(np.int32)
    truth_binary = (truth > 0.5).astype(np.int32)
    
    # 计算交集和并集
    intersection = np.sum(pred_binary * truth_binary)
    union = np.sum(pred_binary) + np.sum(truth_binary)
    
    # 避免除以零，返回NaN
    if union == 0:
        return np.nan
    
    dice = 2.0 * intersection / union
    return dice

def main():
    # 设置路径
    pred_dir = "/media/dell/T7 Shield/nnunet/AllData/HK/mask/HKSZ_38/Couinaud_predicted"
    label_dir = "/media/dell/T7 Shield/nnunet/AllData/HK/mask/Couinaud_modified_HKSZ38"
    output_dir = "/media/dell/T7 Shield/nnunet/AllData/HK/HK_dice值"
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 获取所有预测文件
    pred_files = sorted(glob(os.path.join(pred_dir, "*.nii.gz")))
    
    # 存储结果
    results = []
    
    # 遍历每个预测文件
    for pred_file in pred_files:
        # 获取文件名
        filename = os.path.basename(pred_file)
        
        # 构建对应的标签文件路径
        label_file = os.path.join(label_dir, filename)
        
        # 检查标签文件是否存在
        if not os.path.exists(label_file):
            print(f"警告: 找不到对应的标签文件 {label_file}")
            continue
        
        try:
            # 加载预测和标签数据
            pred_data = load_nifti_file(pred_file)
            label_data = load_nifti_file(label_file)
            
            # 计算Dice系数
            dice_score = calculate_dice(pred_data, label_data)
            
            # 添加到结果列表
            results.append({
                "文件名": filename,
                "Dice系数": dice_score
            })
            
            if np.isnan(dice_score):
                print(f"处理完成: {filename}, Dice系数: NaN (分母为0)")
            else:
                print(f"处理完成: {filename}, Dice系数: {dice_score:.4f}")
            
        except Exception as e:
            print(f"处理文件 {filename} 时出错: {str(e)}")
    
    # 创建DataFrame并保存到Excel
    if results:
        df = pd.DataFrame(results)
        
        # 计算平均Dice系数（忽略NaN值）
        avg_dice = df["Dice系数"].mean(skipna=True)
        
        # 添加平均行
        avg_row = pd.DataFrame({
            "文件名": ["平均值"],
            "Dice系数": [avg_dice]
        })
        df = pd.concat([df, avg_row], ignore_index=True)
        
        excel_path = os.path.join(output_dir, "dice_results.xlsx")
        
        # 保存到Excel，不显示NaN值
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, na_rep='')
        
        print(f"结果已保存到: {excel_path}")
        print(f"平均Dice系数: {avg_dice:.4f} (已忽略NaN值)")
    else:
        print("未找到任何有效文件对进行处理")

if __name__ == "__main__":
    main()