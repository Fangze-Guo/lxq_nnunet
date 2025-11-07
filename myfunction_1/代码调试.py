import pydicom
from pathlib import Path

def simple_accession_check(folder_path):
    """
    简化版本，只输出Accession Number和一致性判断
    """
    folder_path = Path(folder_path)
    
    accession_numbers = set()
    
    print(f"检查目录: {folder_path}")
    print("=" * 50)
    
    # 扫描所有DICOM文件
    for dicom_file in folder_path.rglob("*"):
        if dicom_file.suffix.lower() in ['.dcm', '.dicom'] or dicom_file.is_file():
            try:
                ds = pydicom.dcmread(dicom_file, stop_before_pixels=True)
                if hasattr(ds, 'AccessionNumber') and ds.AccessionNumber:
                    accession_numbers.add(ds.AccessionNumber)
            except:
                continue
    
    # 输出结果
    if accession_numbers:
        print("找到的Accession Number:")
        for acc in accession_numbers:
            print(f"  - {acc}")
        
        if len(accession_numbers) == 1:
            print(f"\n✅ 结果: 所有切片Accession Number相同")
        else:
            print(f"\n❌ 结果: 切片Accession Number不一致 (共{len(accession_numbers)}个不同的值)")
    else:
        print("❌ 未找到任何Accession Number")
    
    return accession_numbers

# 直接运行
if __name__ == "__main__":
    target_folder = "/media/dell/T7 Shield/nnunet/AllData/PKUShZh/finished/HBP/HBP_dicom/2174964/018_t1_vibe_dixon_tra_p4_15min_F"
    simple_accession_check(target_folder)