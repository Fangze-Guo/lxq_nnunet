import pydicom
from pydicom import dcmread
import os

def read_dicom_header(dicom_path):
    """
    读取DICOM文件头信息（不包含图像像素数据）
    """
    try:
        # 检查文件是否存在
        if not os.path.exists(dicom_path):
            print(f"错误: 文件不存在 - {dicom_path}")
            return None
        
        # 读取DICOM文件，不加载像素数据以提高性能
        ds = dcmread(dicom_path, force=True)
        
        print("=" * 70)
        print("DICOM文件表头信息")
        print("=" * 70)
        
        # 患者信息
        print("\n=== 患者信息 ===")
        print(f"患者姓名: {getattr(ds, 'PatientName', 'N/A')}")
        print(f"患者ID: {getattr(ds, 'PatientID', 'N/A')}")
        print(f"患者出生日期: {getattr(ds, 'PatientBirthDate', 'N/A')}")
        print(f"患者性别: {getattr(ds, 'PatientSex', 'N/A')}")
        print(f"患者年龄: {getattr(ds, 'PatientAge', 'N/A')}")
        # 老师要的信息
        
        # 研究信息
        print("\n=== 研究信息 ===")
        print(f"研究日期: {getattr(ds, 'StudyDate', 'N/A')}")
        print(f"研究时间: {getattr(ds, 'StudyTime', 'N/A')}")
        print(f"研究描述: {getattr(ds, 'StudyDescription', 'N/A')}")
        print(f"研究ID: {getattr(ds, 'StudyID', 'N/A')}")
        print(f"研究实例UID: {getattr(ds, 'StudyInstanceUID', 'N/A')}")
        print(f"接入号: {getattr(ds, 'AccessionNumber', 'N/A')}")
        
        # 序列信息
        print("\n=== 序列信息 ===")
        print(f"序列日期: {getattr(ds, 'SeriesDate', 'N/A')}")
        print(f"序列时间: {getattr(ds, 'SeriesTime', 'N/A')}")
        print(f"序列描述: {getattr(ds, 'SeriesDescription', 'N/A')}")
        print(f"序列编号: {getattr(ds, 'SeriesNumber', 'N/A')}")
        print(f"序列实例UID: {getattr(ds, 'SeriesInstanceUID', 'N/A')}")
        print(f"协议名称: {getattr(ds, 'ProtocolName', 'N/A')}")
        
        # 图像信息
        print("\n=== 图像信息 ===")
        print(f"实例编号: {getattr(ds, 'InstanceNumber', 'N/A')}")
        print(f"SOP实例UID: {getattr(ds, 'SOPInstanceUID', 'N/A')}")
        print(f"图像类型: {getattr(ds, 'ImageType', 'N/A')}")
        print(f"模态: {getattr(ds, 'Modality', 'N/A')}")
        print(f"图像位置: {getattr(ds, 'ImagePositionPatient', 'N/A')}")
        print(f"图像方向: {getattr(ds, 'ImageOrientationPatient', 'N/A')}")
        
        # 设备信息
        print("\n=== 设备信息 ===")
        print(f"制造商: {getattr(ds, 'Manufacturer', 'N/A')}")
        print(f"设备型号: {getattr(ds, 'ManufacturerModelName', 'N/A')}")
        print(f"机构名称: {getattr(ds, 'InstitutionName', 'N/A')}")
        print(f"机构地址: {getattr(ds, 'InstitutionAddress', 'N/A')}")
        print(f"工作站名称: {getattr(ds, 'StationName', 'N/A')}")
        
        # 技术参数
        print("\n=== 技术参数 ===")
        print(f"切片厚度: {getattr(ds, 'SliceThickness', 'N/A')}")
        print(f"像素间距: {getattr(ds, 'PixelSpacing', 'N/A')}")
        print(f"图像尺寸: {getattr(ds, 'Rows', 'N/A')} x {getattr(ds, 'Columns', 'N/A')}")
        print(f"位深: {getattr(ds, 'BitsAllocated', 'N/A')} bits")
        print(f"窗宽: {getattr(ds, 'WindowWidth', 'N/A')}")
        print(f"窗位: {getattr(ds, 'WindowCenter', 'N/A')}")
        
        # 其他重要信息
        print("\n=== 其他信息 ===")
        print(f"内容日期: {getattr(ds, 'ContentDate', 'N/A')}")
        print(f"内容时间: {getattr(ds, 'ContentTime', 'N/A')}")
        print(f"转换类型: {getattr(ds, 'ConversionType', 'N/A')}")
        
        return ds
        
    except Exception as e:
        print(f"读取DICOM文件时出错: {str(e)}")
        return None

# 你的DICOM文件路径
dicom_path = "/media/dell/T7 Shield/nnunet/AllData/GXYF/分组数据/组1/0001268446/AT000001.19 6 2133.dcm"

# 执行函数
dataset = read_dicom_header(dicom_path)

# 如果需要查看所有标签的完整列表，可以取消下面的注释
if dataset:
    print("\n" + "=" * 70)
    print("所有DICOM标签列表:")
    print("=" * 70)
    
    for elem in dataset:
        if elem.keyword and elem.keyword not in ['PixelData']:  # 排除像素数据
            value = elem.value
            # 对于长字符串进行截断显示
            if isinstance(value, str) and len(value) > 100:
                value = value[:100] + "..."
            print(f"{elem.tag:10} {elem.keyword:30}: {value}")