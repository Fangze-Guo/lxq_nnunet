import pandas as pd
import os
from openpyxl import load_workbook

def create_subtables_in_excel(dicom_root_path, source_excel_path, output_excel_path):
    """
    在现有Excel文件中创建新的子表格：共同患者数据和Excel有但DICOM无的患者数据
    """
    
    # 检查路径是否存在
    if not os.path.exists(dicom_root_path):
        print(f"错误: DICOM文件夹路径不存在 - {dicom_root_path}")
        return False
    
    if not os.path.exists(source_excel_path):
        print(f"错误: Excel文件路径不存在 - {source_excel_path}")
        return False
    
    # 从DICOM文件夹提取PatientID
    print("正在从DICOM文件夹提取PatientID...")
    dicom_df = extract_patient_ids_from_dicom_folders(dicom_root_path)
    
    if dicom_df.empty:
        print("未从DICOM文件夹中找到任何PatientID")
        return False
    
    print(f"从DICOM文件夹中找到 {len(dicom_df)} 个患者的PatientID")
    
    # 从Excel文件读取数据
    print("正在从Excel文件读取数据...")
    try:
        excel_df = pd.read_excel(source_excel_path)
        
        # 检查是否存在PatientID列
        if 'PatientID' not in excel_df.columns:
            print("错误: Excel文件中没有找到'PatientID'列")
            print(f"可用的列名: {list(excel_df.columns)}")
            return False
            
    except Exception as e:
        print(f"读取Excel文件时出错: {str(e)}")
        return False
    
    print(f"从Excel文件中找到 {len(excel_df)} 个患者的记录")
    
    # 提取PatientID列表
    dicom_patient_ids = set(dicom_df['PatientID'].astype(str).str.strip())
    excel_patient_ids = set(excel_df['PatientID'].astype(str).str.strip())
    
    # 找出交集和差异
    common_patient_ids = dicom_patient_ids.intersection(excel_patient_ids)
    excel_only_patient_ids = excel_patient_ids - dicom_patient_ids
    
    print(f"共同的PatientID数量: {len(common_patient_ids)}")
    print(f"Excel中有但DICOM中没有的PatientID数量: {len(excel_only_patient_ids)}")
    
    # 创建共同患者数据子表格
    common_patients_df = excel_df[excel_df['PatientID'].astype(str).str.strip().isin(common_patient_ids)].copy()
    
    # 添加文件夹信息
    folder_mapping = dicom_df.set_index('PatientID')['FolderName'].to_dict()
    common_patients_df['DICOM文件夹名称'] = common_patients_df['PatientID'].astype(str).str.strip().map(folder_mapping)
    
    # 重新排列列，将文件夹名称放在前面
    cols = ['DICOM文件夹名称', 'PatientID'] + [col for col in common_patients_df.columns if col not in ['DICOM文件夹名称', 'PatientID']]
    common_patients_df = common_patients_df[cols]
    
    # 创建Excel有但DICOM无的患者数据子表格
    excel_only_df = excel_df[excel_df['PatientID'].astype(str).str.strip().isin(excel_only_patient_ids)].copy()
    
    # 创建统计汇总
    summary_data = {
        '统计项': ['DICOM文件夹患者数', 'Excel文件患者数', '共同患者数', 'Excel有但DICOM无'],
        '数量': [len(dicom_patient_ids), len(excel_patient_ids), len(common_patient_ids), len(excel_only_patient_ids)]
    }
    summary_df = pd.DataFrame(summary_data)
    
    # 保存到新的Excel文件
    try:
        with pd.ExcelWriter(output_excel_path, engine='openpyxl') as writer:
            # 保存原始数据
            excel_df.to_excel(writer, sheet_name='原始数据', index=False)
            
            # 保存共同患者数据
            common_patients_df.to_excel(writer, sheet_name='共同患者数据', index=False)
            
            # 保存Excel有但DICOM无的患者数据
            excel_only_df.to_excel(writer, sheet_name='Excel有_DICOM无', index=False)
            
            # 保存统计汇总
            summary_df.to_excel(writer, sheet_name='统计汇总', index=False)
            
            # 保存DICOM文件夹信息（可选）
            dicom_df.to_excel(writer, sheet_name='DICOM文件夹信息', index=False)
        
        print(f"结果已保存到: {output_excel_path}")
        
        # 显示统计信息
        print("\n统计信息:")
        print("=" * 40)
        for _, row in summary_df.iterrows():
            print(f"{row['统计项']}: {row['数量']}")
            
        return True
        
    except Exception as e:
        print(f"保存Excel文件时出错: {str(e)}")
        return False

def extract_patient_ids_from_dicom_folders(root_path):
    """
    从DICOM文件夹结构中提取所有病人的PatientID
    """
    patient_data = []
    
    # 遍历第一级子文件夹（病人文件夹）
    for patient_folder in os.listdir(root_path):
        patient_path = os.path.join(root_path, patient_folder)
        
        if not os.path.isdir(patient_path):
            continue
            
        patient_id = None
        dicom_count = 0
        
        # 递归查找DICOM文件
        for root, dirs, files in os.walk(patient_path):
            for file in files:
                if file.lower().endswith(('.dcm', '.dicom')):
                    dicom_count += 1
                    try:
                        ds = pydicom.dcmread(os.path.join(root, file), force=True)
                        patient_id = getattr(ds, 'PatientID', None)
                        if patient_id:
                            break
                    except Exception as e:
                        continue
            if patient_id:
                break
        
        if patient_id:
            patient_data.append({
                'FolderName': patient_folder,
                'PatientID': patient_id,
                'DICOMCount': dicom_count
            })
        else:
            print(f"警告: 文件夹 {patient_folder} 中未找到有效的DICOM文件")
    
    return pd.DataFrame(patient_data)

def main():
    # 定义路径
    dicom_root_path = "/media/dell/T7 Shield/nnunet/AllData/广东省人民医院/GDPH"
    source_excel_path = "/media/dell/T7 Shield/nnunet/AllData/广东省人民医院/HBP-GDPH_PHLF_处理后数据.xlsx"
    output_excel_path = "/media/dell/T7 Shield/nnunet/AllData/广东省人民医院/患者数据分类结果.xlsx"
    
    # 执行处理
    success = create_subtables_in_excel(dicom_root_path, source_excel_path, output_excel_path)
    
    if success:
        print("\n处理完成！新的子表格已创建在目标Excel文件中")
        print(f"文件位置: {output_excel_path}")
    else:
        print("\n处理失败！")

if __name__ == "__main__":
    import pydicom
    main()