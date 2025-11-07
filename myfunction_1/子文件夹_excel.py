import os
import pandas as pd

def list_subfolders_to_excel(directory_paths, excel_path):
    """
    将多个目录的子文件夹名导出到Excel表格
    
    Args:
        directory_paths: 目录路径列表
        excel_path: 输出的Excel文件路径
    """
    # 创建一个空的DataFrame来存储结果
    result_data = {}
    
    for dir_path in directory_paths:
        # 检查目录是否存在
        if not os.path.exists(dir_path):
            print(f"警告: 目录不存在 - {dir_path}")
            result_data[os.path.basename(dir_path.rstrip('/\\'))] = ["目录不存在"]
            continue
            
        if not os.path.isdir(dir_path):
            print(f"警告: 路径不是目录 - {dir_path}")
            result_data[os.path.basename(dir_path.rstrip('/\\'))] = ["路径不是目录"]
            continue
            
        # 获取目录名称作为列名
        dir_name = os.path.basename(dir_path.rstrip('/\\'))
        
        # 获取目录下的所有子文件夹
        try:
            items = os.listdir(dir_path)
            # 过滤出文件夹（不包括文件）
            folders = [item for item in items if os.path.isdir(os.path.join(dir_path, item))]
            
            result_data[dir_name] = folders
            print(f"已处理目录: {dir_name}, 找到 {len(folders)} 个子文件夹")
            
        except PermissionError:
            print(f"错误: 没有权限访问目录 - {dir_path}")
            result_data[dir_name] = ["无访问权限"]
        except Exception as e:
            print(f"错误: 处理目录时发生异常 - {dir_path}, 错误: {e}")
            result_data[dir_name] = [f"处理错误: {str(e)}"]
    
    # 确定最大长度以便对齐数据
    max_length = max(len(folders) for folders in result_data.values()) if result_data else 0
    
    # 填充数据使所有列长度一致
    for key in result_data:
        result_data[key] = result_data[key] + [''] * (max_length - len(result_data[key]))
    
    # 创建DataFrame
    df = pd.DataFrame(result_data)
    
    # 确保输出目录存在
    os.makedirs(os.path.dirname(excel_path), exist_ok=True)
    
    # 保存到Excel文件
    try:
        df.to_excel(excel_path, index=False)
        print(f"子文件夹列表已成功导出到: {excel_path}")
        print(f"总计处理了 {len(directory_paths)} 个目录")
    except Exception as e:
        print(f"错误: 保存Excel文件时发生异常 - {e}")

# 使用示例
if __name__ == "__main__":
    # 定义目录路径
    directories = [
        "/media/dell/T7 Shield/nnunet/AllData/ST/ST_new",
        "/media/dell/T7 Shield/nnunet/AllData/ST/ST_补充"
    ]
    
    # 定义输出Excel文件路径
    excel_file = "/media/dell/T7 Shield/nnunet/AllData/ST/ST_new.xlsx"
    
    # 执行导出
    list_subfolders_to_excel(directories, excel_file)