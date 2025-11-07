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
        
        # 技术参数 - 老师要的重点信息
        print("\n=== 技术参数 (重点信息) ===")
        print(f"TE(ms): {getattr(ds, 'EchoTime', 'N/A')}")
        print(f"TR(ms): {getattr(ds, 'RepetitionTime', 'N/A')}")
        print(f"翻转角(度): {getattr(ds, 'FlipAngle', 'N/A')}")
        print(f"矩阵: {getattr(ds, 'Rows', 'N/A')} × {getattr(ds, 'Columns', 'N/A')}")
        
        # 计算FOV
        fov_info = calculate_fov(ds)
        print(f"FOV(cm): {fov_info}")
        
        print(f"切片厚度(mm): {getattr(ds, 'SliceThickness', 'N/A')}")
        
        # 切片间距信息
        slice_gap = get_slice_gap(ds)
        print(f"切片间距(mm): {slice_gap}")
        
        print(f"激励次数: {getattr(ds, 'NumberOfAverages', 'N/A')}")
        
        # 获取b值（如果是DWI序列）
        b_value = get_b_value(ds)
        print(f"B值: {b_value}")
        
        # 其他技术参数
        print(f"像素间距: {getattr(ds, 'PixelSpacing', 'N/A')}")
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

def calculate_fov(ds):
    """计算视野FOV"""
    try:
        pixel_spacing = getattr(ds, 'PixelSpacing', None)
        rows = getattr(ds, 'Rows', None)
        columns = getattr(ds, 'Columns', None)
        
        if pixel_spacing and rows and columns:
            fov_x = pixel_spacing[0] * columns / 10  # 转换为cm
            fov_y = pixel_spacing[1] * rows / 10     # 转换为cm
            return f"{fov_x:.1f} × {fov_y:.1f}"
        else:
            return "N/A"
    except:
        return "N/A"

def get_slice_gap(ds):
    """获取切片间距"""
    try:
        # 尝试不同的标签获取切片间距
        slice_gap = getattr(ds, 'SpacingBetweenSlices', None)
        if slice_gap:
            return slice_gap
        
        # 如果没有直接标签，尝试计算
        slice_thickness = getattr(ds, 'SliceThickness', None)
        slice_location = getattr(ds, 'SliceLocation', None)
        
        if slice_thickness and slice_location:
            return f"计算中... (需要多张图像)"
        
        return "N/A"
    except:
        return "N/A"

def get_b_value(ds):
    """获取b值（扩散加权成像）"""
    try:
        # 尝试从不同标签获取b值
        b_value = getattr(ds, 'DiffusionBValue', None)
        if b_value:
            return b_value
            
        # 检查序列描述是否包含DWI信息
        series_desc = getattr(ds, 'SeriesDescription', '')
        if any(word in str(series_desc).upper() for word in ['DWI', 'DIFFUSION']):
            return "存在(需查看具体值)"
            
        return "N/A (非DWI序列)"
    except:
        return "N/A"

def print_all_dicom_tags(ds):
    """打印所有DICOM标签"""
    print("\n" + "=" * 70)
    print("所有DICOM标签列表:")
    print("=" * 70)
    
    tag_count = 0
    for elem in dataset:
        if elem.keyword and elem.keyword not in ['PixelData']:  # 排除像素数据
            tag_count += 1
            value = elem.value
            
            # 对于长字符串进行截断显示
            if isinstance(value, str) and len(value) > 100:
                value = value[:100] + "..."
            elif isinstance(value, bytes):
                value = f"<二进制数据，长度: {len(value)}>"
            elif isinstance(value, list) and len(value) > 5:
                value = str(value[:5]) + "..."
                
            print(f"{elem.tag:10} {elem.keyword:30}: {value}")
    
    print(f"\n总共找到 {tag_count} 个DICOM标签")

# 你的DICOM文件路径
dicom_path = "/media/dell/T7 Shield/nnunet/AllData/GXYF/分组数据/组1/0001268446/AT000001.19 6 2133.dcm"

# 执行函数
dataset = read_dicom_header(dicom_path)

# # 打印所有DICOM标签
# if dataset:
#     print_all_dicom_tags(dataset)
# 额外功能：提取特定参数用于表格
if dataset:
    print("\n" + "=" * 70)
    print("表格格式的参数摘要:")
    print("=" * 70)
    table_params = {
        'MR scanner': f"{getattr(dataset, 'Manufacturer', 'N/A')} {getattr(dataset, 'ManufacturerModelName', 'N/A')}",
        'Sequence': getattr(dataset, 'SeriesDescription', 'N/A'),
        'TE(ms)': getattr(dataset, 'EchoTime', 'N/A'),
        'TR(ms)': getattr(dataset, 'RepetitionTime', 'N/A'),
        'Flip angle(degree)': getattr(dataset, 'FlipAngle', 'N/A'),
        'Matrix': f"{getattr(dataset, 'Rows', 'N/A')}×{getattr(dataset, 'Columns', 'N/A')}",
        'FOV(cm)': calculate_fov(dataset),
        'Slice thickness(mm)': getattr(dataset, 'SliceThickness', 'N/A'),
        'Slice gap(mm)': get_slice_gap(dataset),
        'Number of excitations': getattr(dataset, 'NumberOfAverages', 'N/A'),
        'B values': get_b_value(dataset)
    }
    
    for key, value in table_params.items():
        print(f"{key:<25}: {value}")