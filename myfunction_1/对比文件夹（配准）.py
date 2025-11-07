import os
import argparse
# /media/dell/T7 Shield/nnunet/AllData/配准/HK_HBP(1).xlsx
# /media/dell/T7 Shield/nnunet/AllData/配准/HK_precontrast(1).xlsx
# /media/dell/T7 Shield/nnunet/AllData/配准/PKU_HBP(1).xlsx
# /media/dell/T7 Shield/nnunet/AllData/配准/PKU_precontrast(1).xlsx
# /media/dell/T7 Shield/nnunet/AllData/配准/ST_HBP(2).xlsx
# /media/dell/T7 Shield/nnunet/AllData/配准/ST_precontrast(1).xlsx
import pandas as pd

# 读取两个Excel文件
file1_path = "/media/dell/T7 Shield/nnunet/AllData/配准/HK_HBP(1).xlsx"
file2_path = "/media/dell/T7 Shield/nnunet/AllData/配准/HK_precontrast(1).xlsx"

try:
    # 读取Excel文件
    df1 = pd.read_excel(file1_path)
    df2 = pd.read_excel(file2_path)
    
    # 手动指定列名 - 请根据您的实际列名修改这里
    folder_col1 = "文件名"    # 第一个表格中文件夹名的列名
    slice_col1 = "切片个数"     # 第一个表格中切片个数的列名
    folder_col2 = "文件名"    # 第二个表格中文件夹名的列名
    slice_col2 = "切片个数"     # 第二个表格中切片个数的列名
    
    # 合并两个表格，基于文件夹名
    merged_df = pd.merge(df1, df2, left_on=folder_col1, right_on=folder_col2, 
                       suffixes=('_HBP', '_precontrast'))
    
    # 找出切片个数不同的行
    different_slices = merged_df[merged_df[slice_col1 + '_HBP'] != merged_df[slice_col2 + '_precontrast']]
    
    print(f"找到 {len(different_slices)} 个文件夹的切片个数不同:")
    
    if len(different_slices) > 0:
        # 输出结果
        result_df = different_slices[[folder_col1, 
                                    slice_col1 + '_HBP', 
                                    slice_col2 + '_precontrast']].copy()
        result_df.columns = ['文件夹名', 'HBP_切片个数', 'Precontrast_切片个数']
        
        print("\n不相同的文件夹名及切片个数:")
        for _, row in result_df.iterrows():
            print(f"文件夹: {row['文件夹名']}, HBP: {row['HBP_切片个数']}, Precontrast: {row['Precontrast_切片个数']}")
        
        # 保存结果到Excel文件（可选）
        result_df.to_excel("切片个数不同的文件夹.xlsx", index=False)
        print("\n结果已保存到 '切片个数不同的文件夹.xlsx'")
    else:
        print("所有相同文件夹名的切片个数都相同")
        
except FileNotFoundError as e:
    print(f"文件未找到: {e}")
    print("请检查文件路径是否正确")
except Exception as e:
    print(f"处理过程中出现错误: {e}")