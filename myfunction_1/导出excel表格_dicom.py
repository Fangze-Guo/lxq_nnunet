import pydicom
from pydicom import dcmread
import os
import pandas as pd
from pathlib import Path
import warnings
from datetime import datetime

# 忽略pydicom的警告
warnings.filterwarnings("ignore", category=UserWarning, module="pydicom.valuerep")


def read_dicom_header(dicom_path):
    """
    读取DICOM文件头信息
    """
    try:
        # 只读取文件头，不读取像素数据以提高性能
        ds = dcmread(dicom_path, force=True, stop_before_pixels=True)
        return ds
    except Exception as e:
        print(f"    错误：无法读取DICOM文件 {dicom_path}: {str(e)}")
        return None


def extract_patient_info_from_dicom(ds, patient_folder, sequence_folder, dicom_file):
    """
    从DICOM数据集中提取病人和序列信息
    """
    info = {
        '病人文件夹': patient_folder,
        '序列文件夹': sequence_folder,
        'DICOM文件': dicom_file,
        '患者姓名': 'N/A',  # 默认值，如果出错就保持N/A
        '患者ID': getattr(ds, 'PatientID', 'N/A'),
        '患者性别': getattr(ds, 'PatientSex', 'N/A'),
        '患者年龄': getattr(ds, 'PatientAge', 'N/A'),
        '研究日期': format_date(getattr(ds, 'StudyDate', 'N/A')),
        '序列描述': getattr(ds, 'SeriesDescription', sequence_folder),  # 默认使用文件夹名
        '序列编号': getattr(ds, 'SeriesNumber', 'N/A'),
        '模态': getattr(ds, 'Modality', 'N/A'),
        '制造商': getattr(ds, 'Manufacturer', 'N/A'),
        '设备型号': getattr(ds, 'ManufacturerModelName', 'N/A'),
    }

    # 安全地获取患者姓名（如果出错就跳过）
    try:
        if hasattr(ds, 'PatientName'):
            patient_name = getattr(ds, 'PatientName')
            # 处理可能的DICOM PersonName对象
            if hasattr(patient_name, 'family_name') and hasattr(patient_name, 'given_name'):
                # 格式化为"姓 名"
                family_name = patient_name.family_name or ''
                given_name = patient_name.given_name or ''
                info['患者姓名'] = f"{family_name} {given_name}".strip()
            else:
                info['患者姓名'] = str(patient_name)
    except Exception as e:
        print(f"    警告：无法读取患者姓名，跳过: {str(e)}")
        info['患者姓名'] = 'N/A'

    # MRI特定参数
    if hasattr(ds, 'EchoTime'):
        info['TE(ms)'] = safe_convert_float(getattr(ds, 'EchoTime', 'N/A'))
    else:
        info['TE(ms)'] = 'N/A'

    if hasattr(ds, 'RepetitionTime'):
        info['TR(ms)'] = safe_convert_float(getattr(ds, 'RepetitionTime', 'N/A'))
    else:
        info['TR(ms)'] = 'N/A'

    if hasattr(ds, 'FlipAngle'):
        info['翻转角(度)'] = safe_convert_float(getattr(ds, 'FlipAngle', 'N/A'))
    else:
        info['翻转角(度)'] = 'N/A'

    # 图像几何参数
    if hasattr(ds, 'Rows') and hasattr(ds, 'Columns'):
        info['矩阵'] = f"{getattr(ds, 'Rows', '')}×{getattr(ds, 'Columns', '')}"
    else:
        info['矩阵'] = 'N/A'

    # FOV计算
    if hasattr(ds, 'Rows') and hasattr(ds, 'Columns') and hasattr(ds, 'PixelSpacing'):
        try:
            pixel_spacing = ds.PixelSpacing
            if len(pixel_spacing) >= 2:
                fov_x = float(ds.Columns) * float(pixel_spacing[0]) / 10  # 转换为cm
                fov_y = float(ds.Rows) * float(pixel_spacing[1]) / 10  # 转换为cm
                info['FOV(cm)'] = f"{fov_x:.1f}×{fov_y:.1f}"
            else:
                info['FOV(cm)'] = 'N/A'
        except:
            info['FOV(cm)'] = 'N/A'
    else:
        info['FOV(cm)'] = 'N/A'

    # 切片参数
    if hasattr(ds, 'SliceThickness'):
        info['切片厚度(mm)'] = safe_convert_float(getattr(ds, 'SliceThickness', 'N/A'))
    else:
        info['切片厚度(mm)'] = 'N/A'

    if hasattr(ds, 'SpacingBetweenSlices'):
        info['切片间距(mm)'] = safe_convert_float(getattr(ds, 'SpacingBetweenSlices', 'N/A'))
    else:
        info['切片间距(mm)'] = 'N/A'

    # 其他参数
    if hasattr(ds, 'NumberOfAverages'):
        info['激励次数'] = safe_convert_float(getattr(ds, 'NumberOfAverages', 'N/A'))
    else:
        info['激励次数'] = 'N/A'

    # DWI相关参数
    if hasattr(ds, 'DiffusionBValue'):
        info['B值'] = safe_convert_float(getattr(ds, 'DiffusionBValue', 'N/A'))
    else:
        info['B值'] = 'N/A'

    # 像素信息
    if hasattr(ds, 'PixelSpacing'):
        try:
            pixel_spacing = ds.PixelSpacing
            if len(pixel_spacing) >= 2:
                info['像素间距'] = f"{float(pixel_spacing[0]):.3f}×{float(pixel_spacing[1]):.3f} mm"
            else:
                info['像素间距'] = 'N/A'
        except:
            info['像素间距'] = 'N/A'
    else:
        info['像素间距'] = 'N/A'

    if hasattr(ds, 'BitsStored'):
        info['位深'] = getattr(ds, 'BitsStored', 'N/A')
    else:
        info['位深'] = 'N/A'

    return info


def safe_convert_float(value, default='N/A'):
    """
    安全地将值转换为浮点数
    """
    if value == 'N/A' or value is None:
        return default

    try:
        # 如果已经是数字类型，直接返回
        if isinstance(value, (int, float)):
            return float(value)

        # 如果是字符串，尝试转换
        if isinstance(value, str):
            # 处理可能包含单位的字符串
            value = value.strip()
            # 移除常见的单位
            for unit in ['ms', '°', 'deg', 'mm', 'cm']:
                if value.lower().endswith(unit):
                    value = value[:-len(unit)].strip()
            return float(value)

        return float(value)
    except (ValueError, TypeError):
        return default


def format_date(date_str):
    """
    格式化日期字符串
    """
    if date_str == 'N/A' or not date_str:
        return 'N/A'

    try:
        # DICOM日期格式通常是YYYYMMDD
        if len(date_str) == 8:
            date_obj = datetime.strptime(date_str, '%Y%m%d')
            return date_obj.strftime('%Y-%m-%d')
        else:
            return date_str
    except:
        return date_str


def is_dicom_file(file_path):
    """
    可靠地检测文件是否为DICOM文件 - 改进版本
    """
    try:
        # 检查文件是否存在且可读
        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            return False

        # 检查文件大小，避免读取空文件或极小文件
        file_size = os.path.getsize(file_path)
        if file_size < 132:  # DICOM文件头最小长度
            return False

        # 多种验证方法结合
        with open(file_path, 'rb') as f:
            # 方法1: 检查DICOM前缀（128字节的preamble + 4字节的"DICM"）
            f.seek(128)
            prefix = f.read(4)
            if prefix == b'DICM':
                return True

            # 方法2: 检查文件开头是否有DICOM标签（通常是0002,0000等）
            f.seek(0)
            first_bytes = f.read(8)
            # 检查是否包含常见的DICOM标签模式
            if len(first_bytes) >= 8:
                # 检查是否像DICOM标签结构（组号+元素号）
                group_number = first_bytes[0:2]
                element_number = first_bytes[2:4]
                # 如果看起来像有效的DICOM标签结构
                if group_number in [b'\x02\x00', b'\x08\x00', b'\x10\x00']:
                    return True

        # 方法3: 尝试用pydicom读取（最后的手段）
        try:
            ds = dcmread(file_path, force=True, stop_before_pixels=True)
            # 检查是否有必需的DICOM属性
            if (hasattr(ds, 'SOPClassUID') or
                    hasattr(ds, 'Modality') or
                    hasattr(ds, 'StudyDate')):
                return True
        except:
            pass

        return False

    except Exception as e:
        print(f"    检测DICOM文件时出错 {os.path.basename(file_path)}: {str(e)}")
        return False


def find_dicom_files(folder_path):
    """
    在文件夹中查找DICOM文件，跳过.txt文件，优先选择.dcm文件
    """
    dicom_files = []
    dcm_files = []  # 专门存储.dcm文件
    other_dicom_files = []  # 存储其他格式的DICOM文件

    try:
        for file in os.listdir(folder_path):
            file_path = os.path.join(folder_path, file)

            # 只处理文件，跳过目录
            if not os.path.isfile(file_path):
                continue

            # 跳过.txt文件
            if file.lower().endswith('.txt'):
                print(f"    跳过文本文件: {file}")
                continue

            # 检查文件扩展名
            ext = os.path.splitext(file)[1].lower()

            # 如果是.dcm文件，优先考虑
            if ext == '.dcm':
                if is_dicom_file(file_path):
                    dcm_files.append(file)
                    print(f"    ✅ 找到.dcm文件: {file}")
                else:
                    print(f"    ❌ 不是有效的DICOM文件: {file}")
            # 其他可能的DICOM扩展名或无扩展名
            elif ext in ['.dicom', '.dcim', '.ima', ''] or file.startswith('I') or file.endswith('.Seq'):
                if is_dicom_file(file_path):
                    other_dicom_files.append(file)
                    print(f"    ✅ 找到DICOM文件: {file} (扩展名: {ext})")
                else:
                    print(f"    ❌ 不是DICOM文件: {file}")
            else:
                # 对于其他扩展名的文件，也尝试检测是否为DICOM
                if is_dicom_file(file_path):
                    other_dicom_files.append(file)
                    print(f"    ✅ 找到DICOM文件: {file} (非常见扩展名)")
                else:
                    print(f"    跳过非DICOM文件: {file} (扩展名: {ext})")

    except Exception as e:
        print(f"读取文件夹 {folder_path} 时出错: {str(e)}")

    # 优先返回.dcm文件，如果没有则返回其他DICOM文件
    if dcm_files:
        return dcm_files
    else:
        return other_dicom_files


def select_dicom_file(dicom_files, folder_path):
    """
    从DICOM文件列表中选择一个文件
    优先选择.dcm文件，如果有多个则选择第一个
    """
    if not dicom_files:
        return None

    # 分离.dcm文件和其他DICOM文件
    dcm_files = [f for f in dicom_files if f.lower().endswith('.dcm')]
    other_files = [f for f in dicom_files if not f.lower().endswith('.dcm')]

    # 优先选择.dcm文件
    if dcm_files:
        selected_file = dcm_files[0]
        print(f"    🎯 选择.dcm文件: {selected_file}")

        # 如果有多个.dcm文件，显示信息
        if len(dcm_files) > 1:
            print(f"    注意: 文件夹中有 {len(dcm_files)} 个.dcm文件，选择第一个: {selected_file}")

        return selected_file
    elif other_files:
        selected_file = other_files[0]
        print(f"    🎯 选择DICOM文件: {selected_file}")

        # 对于类似 "1267524.Seq21.Ser19.Img1.dcm" 的文件，尝试其他文件
        if selected_file.lower().endswith('.dcm') and not is_dicom_file(os.path.join(folder_path, selected_file)):
            print(f"    ⚠️ 选择的文件可能不是有效DICOM，尝试其他文件...")
            for other_file in other_files[1:]:
                other_file_path = os.path.join(folder_path, other_file)
                if is_dicom_file(other_file_path):
                    print(f"    🎯 重新选择有效的DICOM文件: {other_file}")
                    return other_file

        return selected_file
    else:
        return None


def is_folder_empty(folder_path):
    """
    检查文件夹是否为空
    """
    try:
        if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
            return True

        items = list(os.listdir(folder_path))
        return len(items) == 0
    except (PermissionError, OSError):
        # 如果无法访问文件夹，视为非空
        return False


def find_empty_folders(root_directory):
    """
    查找所有空文件夹
    """
    empty_folders = {
        '一级空文件夹': [],  # 直接在一级目录下的空文件夹
        '二级空文件夹': [],  # 在一级文件夹下的空二级文件夹
        '无DICOM文件的序列文件夹': []  # 包含文件但没有DICOM文件的序列文件夹
    }

    print("\n" + "=" * 60)
    print("开始检测空文件夹...")
    print("=" * 60)

    try:
        # 检查一级文件夹
        patient_folders = [f for f in os.listdir(root_directory)
                           if os.path.isdir(os.path.join(root_directory, f))]

        for patient_folder in patient_folders:
            patient_path = os.path.join(root_directory, patient_folder)

            # 检查一级文件夹是否为空
            if is_folder_empty(patient_path):
                empty_folders['一级空文件夹'].append(patient_folder)
                print(f"❌ 一级空文件夹: {patient_folder}")
                continue

            # 检查二级文件夹
            try:
                sequence_folders = [f for f in os.listdir(patient_path)
                                    if os.path.isdir(os.path.join(patient_path, f))]

                if not sequence_folders:
                    # 一级文件夹下没有二级文件夹，但可能有文件
                    empty_folders['二级空文件夹'].append(f"{patient_folder} (无二级文件夹)")
                    print(f"❌ 无二级文件夹: {patient_folder}")
                    continue

                for sequence_folder in sequence_folders:
                    sequence_path = os.path.join(patient_path, sequence_folder)

                    # 检查二级文件夹是否为空
                    if is_folder_empty(sequence_path):
                        empty_folders['二级空文件夹'].append(f"{patient_folder}/{sequence_folder}")
                        print(f"❌ 二级空文件夹: {patient_folder}/{sequence_folder}")
                        continue

                    # 检查是否有DICOM文件
                    dicom_files = find_dicom_files(sequence_path)
                    if not dicom_files:
                        empty_folders['无DICOM文件的序列文件夹'].append(f"{patient_folder}/{sequence_folder}")
                        print(f"⚠️  无DICOM文件: {patient_folder}/{sequence_folder}")

            except Exception as e:
                print(f"警告：无法访问病人文件夹 {patient_folder}: {str(e)}")
                continue

    except Exception as e:
        print(f"错误：读取根目录失败 - {str(e)}")

    return empty_folders


def save_empty_folders_report(empty_folders, output_path):
    """
    保存空文件夹报告到Excel
    """
    try:
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # 保存一级空文件夹
            if empty_folders['一级空文件夹']:
                df1 = pd.DataFrame({
                    '一级空文件夹': empty_folders['一级空文件夹'],
                    '类型': '一级空文件夹',
                    '检查时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
                df1.to_excel(writer, sheet_name='一级空文件夹', index=False)

            # 保存二级空文件夹
            if empty_folders['二级空文件夹']:
                df2 = pd.DataFrame({
                    '二级空文件夹': empty_folders['二级空文件夹'],
                    '类型': '二级空文件夹',
                    '检查时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
                df2.to_excel(writer, sheet_name='二级空文件夹', index=False)

            # 保存无DICOM文件的序列文件夹
            if empty_folders['无DICOM文件的序列文件夹']:
                df3 = pd.DataFrame({
                    '无DICOM文件的序列文件夹': empty_folders['无DICOM文件的序列文件夹'],
                    '类型': '无DICOM文件',
                    '检查时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
                df3.to_excel(writer, sheet_name='无DICOM文件序列', index=False)

        print(f"✅ 空文件夹报告已保存到: {output_path}")

    except Exception as e:
        print(f"❌ 保存空文件夹报告时出错: {str(e)}")
        # 尝试保存为CSV
        try:
            csv_path = output_path.replace('.xlsx', '_empty_folders.csv')
            all_empty = (empty_folders['一级空文件夹'] +
                         empty_folders['二级空文件夹'] +
                         empty_folders['无DICOM文件的序列文件夹'])

            if all_empty:
                df = pd.DataFrame({
                    '空文件夹路径': all_empty,
                    '检查时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
                df.to_csv(csv_path, index=False, encoding='utf-8-sig')
                print(f"✅ 空文件夹报告已保存为CSV: {csv_path}")
        except Exception as e2:
            print(f"❌ 保存CSV文件也失败: {str(e2)}")


def process_patient_folders_enhanced(root_directory, output_excel_path):
    """
    增强的处理函数：跳过.txt文件，优先选择.dcm文件
    """
    all_patient_data = []

    # 获取所有一级子文件夹（每个子文件夹代表一个病人）
    try:
        patient_folders = [f for f in os.listdir(root_directory)
                           if os.path.isdir(os.path.join(root_directory, f))]
        patient_folders.sort()
    except Exception as e:
        print(f"错误：读取根目录失败 - {str(e)}")
        return

    print(f"找到 {len(patient_folders)} 个病人文件夹")
    print("开始处理DICOM文件（跳过.txt文件，优先选择.dcm文件）...")

    total_patients_processed = 0
    total_sequences_processed = 0

    for i, patient_folder in enumerate(patient_folders, 1):
        patient_path = os.path.join(root_directory, patient_folder)
        print(f"\n[{i}/{len(patient_folders)}] 处理病人: {patient_folder}")

        # 获取二级子文件夹（序列文件夹）
        try:
            sequence_folders = [f for f in os.listdir(patient_path)
                                if os.path.isdir(os.path.join(patient_path, f))]
            sequence_folders.sort()
        except Exception as e:
            print(f"  警告：无法访问病人文件夹 {patient_folder}: {str(e)}")
            continue

        if not sequence_folders:
            print(f"  警告：在 {patient_folder} 中未找到序列文件夹")
            continue

        patient_has_data = False

        # 处理每个序列文件夹
        for j, sequence_folder in enumerate(sequence_folders, 1):
            sequence_path = os.path.join(patient_path, sequence_folder)
            print(f"  序列 [{j}/{len(sequence_folders)}]: {sequence_folder}")

            # 查找DICOM文件（跳过.txt文件）
            dicom_files = find_dicom_files(sequence_path)

            if not dicom_files:
                print(f"    警告：在 {sequence_folder} 中未找到DICOM文件")
                # 添加空记录
                empty_info = {
                    '病人文件夹': patient_folder,
                    '序列文件夹': sequence_folder,
                    'DICOM文件': '未找到DICOM文件',
                    '患者姓名': 'N/A',
                    '患者ID': 'N/A',
                    '序列描述': sequence_folder,
                    '模态': 'N/A'
                }
                all_patient_data.append(empty_info)
                continue

            # 选择DICOM文件（优先选择.dcm文件）
            selected_dicom = select_dicom_file(dicom_files, sequence_path)

            if not selected_dicom:
                print(f"    错误：无法选择DICOM文件")
                continue

            # 读取DICOM文件头信息
            dicom_path = os.path.join(sequence_path, selected_dicom)
            ds = read_dicom_header(dicom_path)

            if ds:
                # 提取病人信息
                patient_info = extract_patient_info_from_dicom(ds, patient_folder, sequence_folder, selected_dicom)
                all_patient_data.append(patient_info)
                patient_has_data = True
                total_sequences_processed += 1

                patient_name = patient_info['患者姓名']
                patient_id = patient_info['患者ID']
                series_desc = patient_info['序列描述']
                print(f"    ✅ 成功提取信息: {patient_name} - {patient_id} - {series_desc}")
            else:
                print(f"    ❌ 错误：无法读取DICOM文件 {selected_dicom}")
                # 添加错误记录
                error_info = {
                    '病人文件夹': patient_folder,
                    '序列文件夹': sequence_folder,
                    'DICOM文件': selected_dicom,
                    '患者姓名': '读取错误',
                    '患者ID': '读取错误',
                    '序列描述': sequence_folder,
                    '模态': '读取错误'
                }
                all_patient_data.append(error_info)

        if patient_has_data:
            total_patients_processed += 1

    # 生成Excel文件
    if all_patient_data:
        try:
            df = pd.DataFrame(all_patient_data)

            # 重新排列列的顺序，使重要信息在前
            preferred_order = [
                '病人文件夹', '序列文件夹', 'DICOM文件', '患者姓名', '患者ID', '患者性别', '患者年龄',
                '研究日期', '序列描述', '序列编号', '模态', '制造商', '设备型号',
                'TE(ms)', 'TR(ms)', '翻转角(度)', '矩阵', 'FOV(cm)', '切片厚度(mm)',
                '切片间距(mm)', '激励次数', 'B值', '像素间距', '位深'
            ]

            # 只保留存在的列
            existing_columns = [col for col in preferred_order if col in df.columns]
            # 添加其他列
            other_columns = [col for col in df.columns if col not in preferred_order]
            final_order = existing_columns + other_columns

            df = df[final_order]

            # 保存为Excel文件
            df.to_excel(output_excel_path, index=False, engine='openpyxl')
            print(f"\n✅ 成功生成Excel文件: {output_excel_path}")
            print(f"📊 统计信息:")
            print(f"  总病人文件夹: {len(patient_folders)} 个")
            print(f"  成功处理的病人: {total_patients_processed} 个")
            print(f"  成功提取的序列: {total_sequences_processed} 个")
            print(f"  总记录数: {len(all_patient_data)} 条")

        except Exception as e:
            print(f"❌ 生成Excel文件时出错: {str(e)}")
    else:
        print("❌ 未找到任何可用的病人数据")


def debug_folder_contents(folder_path):
    """
    调试函数：显示文件夹内容
    """
    print(f"\n=== 调试文件夹内容: {folder_path} ===")

    if not os.path.exists(folder_path):
        print("❌ 文件夹不存在")
        return

    try:
        items = os.listdir(folder_path)
        print(f"文件夹中有 {len(items)} 个项:")

        for i, item in enumerate(items):
            item_path = os.path.join(folder_path, item)
            if os.path.isfile(item_path):
                file_size = os.path.getsize(item_path)
                ext = os.path.splitext(item)[1].lower()
                file_type = "📄 文件"

                if ext == '.txt':
                    file_type = "📝 文本文件"
                elif ext == '.dcm':
                    # 检查是否是有效DICOM
                    if is_dicom_file(item_path):
                        file_type = "🩻 有效DICOM文件"
                    else:
                        file_type = "❌ 无效DICOM文件"
                elif ext in ['.dicom', '.dcim', '.ima']:
                    file_type = "📊 可能DICOM文件"

                print(f"  {i + 1:2d}. {file_type}: {item:<30} {file_size:8} bytes")
            else:
                print(f"  {i + 1:2d}. 📁 文件夹: {item}")

    except Exception as e:
        print(f"读取文件夹出错: {str(e)}")


def main_enhanced():
    """
    增强版主函数
    """
    root_directory = "/media/dell/T7 Shield/nnunet/AllData/ST/finished/HBP/HBP_dicom"
    output_excel_path = "/media/dell/T7 Shield/nnunet/AllData/ST/finished/HBP/ST_95.xlsx"
    empty_report_path = "/media/dell/T7 Shield/nnunet/AllData/ST/finished/HBP/ST_kong.xlsx"

    print("开始处理DICOM病人数据（增强版）...")
    print(f"源目录: {root_directory}")
    print(f"输出文件: {output_excel_path}")
    print("功能特性:")
    print("  ✅ 跳过.txt文件")
    print("  ✅ 优先选择.dcm文件")
    print("  ✅ 自动选择第一个.dcm文件")
    print("  ✅ 包含患者姓名（出错时跳过）")
    print("  ✅ 改进的DICOM文件验证")
    print("  ✅ 检测空文件夹")
    print("=" * 60)

    # 调试根目录内容
    debug_folder_contents(root_directory)

    # 检查根目录是否存在
    if not os.path.exists(root_directory):
        print(f"❌ 错误：根目录不存在 - {root_directory}")
        return

    # 处理所有病人文件夹
    process_patient_folders_enhanced(root_directory, output_excel_path)

    # 检测空文件夹
    empty_folders = find_empty_folders(root_directory)

    # 保存空文件夹报告
    if (empty_folders['一级空文件夹'] or
            empty_folders['二级空文件夹'] or
            empty_folders['无DICOM文件的序列文件夹']):

        save_empty_folders_report(empty_folders, empty_report_path)

        # 显示统计信息
        print(f"\n📊 空文件夹统计:")
        print(f"  一级空文件夹: {len(empty_folders['一级空文件夹'])} 个")
        print(f"  二级空文件夹: {len(empty_folders['二级空文件夹'])} 个")
        print(f"  无DICOM文件的序列文件夹: {len(empty_folders['无DICOM文件的序列文件夹'])} 个")

        # 显示空文件夹列表
        if empty_folders['一级空文件夹']:
            print(f"\n一级空文件夹列表:")
            for folder in empty_folders['一级空文件夹']:
                print(f"  - {folder}")

        if empty_folders['二级空文件夹']:
            print(f"\n二级空文件夹列表:")
            for folder in empty_folders['二级空文件夹']:
                print(f"  - {folder}")

        if empty_folders['无DICOM文件的序列文件夹']:
            print(f"\n无DICOM文件的序列文件夹列表:")
            for folder in empty_folders['无DICOM文件的序列文件夹']:
                print(f"  - {folder}")
    else:
        print(f"\n✅ 未发现空文件夹！")

    print("\n处理完成！")


# 单独测试某个序列文件夹
def test_specific_sequence():
    """
    测试特定的序列文件夹
    """
    test_path = r"H:\nnunet\AllData\ST\ST_new_肝胆特异\具体的病人文件夹\具体的序列文件夹"

    if os.path.exists(test_path):
        print(f"测试文件夹: {test_path}")
        debug_folder_contents(test_path)

        print("\n查找DICOM文件:")
        dicom_files = find_dicom_files(test_path)
        print(f"找到 {len(dicom_files)} 个DICOM文件: {dicom_files}")

        if dicom_files:
            selected = select_dicom_file(dicom_files, test_path)
            print(f"选择的文件: {selected}")

            # 测试文件是否是有效DICOM
            if selected:
                file_path = os.path.join(test_path, selected)
                print(f"是否是有效DICOM: {is_dicom_file(file_path)}")
    else:
        print(f"测试文件夹不存在: {test_path}")


if __name__ == "__main__":
    # 运行增强版主程序
    main_enhanced()

    # 如果需要测试特定文件夹，取消下面的注释
    # test_specific_sequence()