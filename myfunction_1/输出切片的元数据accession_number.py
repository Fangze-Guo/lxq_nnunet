import pydicom
from pathlib import Path
import pandas as pd

def quick_accession_to_excel(root_directory):
    """
    快速提取并保存到Excel
    """
    root_path = Path(root_directory)
    patient_data = []
    
    print("正在提取Accession Number...")
    
    for patient_folder in root_path.iterdir():
        if patient_folder.is_dir():
            patient_id = patient_folder.name
            accession_number = "Not Found"
            
            for dicom_file in patient_folder.rglob("*"):
                if dicom_file.suffix.lower() in ['.dcm', '.dicom']:
                    try:
                        ds = pydicom.dcmread(dicom_file, stop_before_pixels=True)
                        if hasattr(ds, 'AccessionNumber') and ds.AccessionNumber:
                            accession_number = ds.AccessionNumber
                            break
                    except:
                        continue
            
            patient_data.append({
                'PatientID': patient_id,
                'AccessionNumber': accession_number
            })
    
    # 保存到Excel
    df = pd.DataFrame(patient_data)
    output_file = "/media/dell/T7 Shield/nnunet/AllData/PKUShZh/finished/HBP/PKU_accession_number_HBP.xlsx"
    df.to_excel(output_file, index=False)
    
    print(f"✅ 完成！共处理 {len(patient_data)} 个患者")
    print(f"✅ 结果已保存到: {output_file}")
    
    return df

# 运行简化版本
if __name__ == "__main__":
    root_dir = "/media/dell/T7 Shield/nnunet/AllData/PKUShZh/finished/HBP/HBP_dicom"
    quick_accession_to_excel(root_dir)