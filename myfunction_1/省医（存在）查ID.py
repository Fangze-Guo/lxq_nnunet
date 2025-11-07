import os
import pydicom
from pydicom import dcmread
import pandas as pd

def extract_patient_ids_from_dicom(root_path):
    """
    从DICOM文件中提取每个病人的PatientID
    """
    patient_data = []
    
    # 遍历第一级子文件夹（病人文件夹）
    for patient_folder in os.listdir(root_path):
        patient_path = os.path.join(root_path, patient_folder)
        
        if not os.path.isdir(patient_path):
            continue
            
        print(f"处理病人文件夹: {patient_folder}")
        
        # 在病人文件夹中查找DICOM文件
        patient_id = None
        dicom_file_path = None
        
        # 递归查找DICOM文件
        for root, dirs, files in os.walk(patient_path):
            for file in files:
                if file.lower().endswith('.dcm'):
                    dicom_file_path = os.path.join(root, file)
                    try:
                        # 读取DICOM文件头信息
                        ds = dcmread(dicom_file_path, force=True)
                        patient_id = getattr(ds, 'PatientID', None)
                        if patient_id:
                            break
                    except Exception as e:
                        print(f"  读取DICOM文件失败: {file} - {e}")
                        continue
            if patient_id:
                break
        
        if patient_id:
            patient_data.append({
                'PatientFolder': patient_folder,
                'PatientID': patient_id,
                'DICOMFile': dicom_file_path
            })
            print(f"  找到PatientID: {patient_id}")
        else:
            print(f"  未找到有效的DICOM文件或PatientID")
    
    return patient_data

def process_patient_directories(root_path):
    """
    处理所有病人目录并输出结果
    """
    print("开始处理病人目录...")
    print("=" * 60)
    
    # 提取PatientID数据
    patient_data = extract_patient_ids_from_dicom(root_path)
    
    # 输出结果
    print("\n" + "=" * 60)
    print("处理结果:")
    print("=" * 60)
    
    if not patient_data:
        print("未找到任何病人的PatientID")
        return
    
    # 创建DataFrame以便更好地显示
    df = pd.DataFrame(patient_data)
    
    # 输出到控制台
    for i, row in df.iterrows():
        print(f"{i+1:3d}. 文件夹: {row['PatientFolder']} -> PatientID: {row['PatientID']}")
    
    # 统计信息
    print("\n" + "=" * 60)
    print("统计信息:")
    print(f"总病人文件夹数: {len([d for d in os.listdir(root_path) if os.path.isdir(os.path.join(root_path, d))])}")
    print(f"成功提取PatientID数: {len(patient_data)}")
    print(f"唯一PatientID数: {df['PatientID'].nunique()}")
    
    # 保存结果到Excel文件
    output_file = "patient_ids_summary.xlsx"
    df.to_excel(output_file, index=False)
    print(f"\n结果已保存到: {output_file}")
    
    return df

# 更高效的版本，使用多线程处理（可选）
def extract_patient_ids_parallel(root_path):
    """
    使用多线程加速处理（适用于大量文件）
    """
    import concurrent.futures
    
    patient_folders = []
    for item in os.listdir(root_path):
        item_path = os.path.join(root_path, item)
        if os.path.isdir(item_path):
            patient_folders.append(item)
    
    def process_single_patient(patient_folder):
        patient_path = os.path.join(root_path, patient_folder)
        patient_id = None
        dicom_file_path = None
        
        for root, dirs, files in os.walk(patient_path):
            for file in files:
                if file.lower().endswith(('.dcm', '.dicom')):
                    try:
                        ds = dcmread(os.path.join(root, file), force=True)
                        patient_id = getattr(ds, 'PatientID', None)
                        if patient_id:
                            dicom_file_path = os.path.join(root, file)
                            break
                    except:
                        continue
            if patient_id:
                break
        
        return {
            'PatientFolder': patient_folder,
            'PatientID': patient_id,
            'DICOMFile': dicom_file_path
        }
    
    # 使用线程池并行处理
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(process_single_patient, patient_folders))
    
    return results
# 主程序
if __name__ == "__main__":
    # 你的根目录路径
    root_path = "/media/dell/T7 Shield/nnunet/AllData/广东省人民医院/GDPH"
    
    # 检查路径是否存在
    if not os.path.exists(root_path):
        print(f"错误: 路径不存在 - {root_path}")
    else:
        # 使用基本版本
        df = process_patient_directories(root_path)
        
        # 如果需要处理大量文件，可以使用并行版本（取消注释下面一行）
        # patient_data = extract_patient_ids_parallel(root_path)