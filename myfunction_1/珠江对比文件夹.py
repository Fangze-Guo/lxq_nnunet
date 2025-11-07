import os
import pandas as pd
from pathlib import Path
import openpyxl


def get_subfolder_names(directory_path):
    """
    获取指定目录下所有子文件夹的名称（仅一级子文件夹）
    
    :param directory_path: 目录路径
    :return: 子文件夹名称集合
    """
    dir_path = Path(directory_path)
    if not dir_path.exists():
        print(f"警告：目录 {directory_path} 不存在")
        return set()
    
    # 获取所有一级子文件夹名称
    subfolders = set()
    for item in dir_path.iterdir():
        if item.is_dir():
            subfolders.add(item.name)
    
    return subfolders


def compare_folders_and_export_to_excel(original_dir, normalized_dir, output_excel_path):
    """
    对比两个目录的子文件夹命名，将normalized_dir中没有的子文件夹输出到Excel
    
    :param original_dir: 原始数据目录
    :param normalized_dir: 命名规范化目录
    :param output_excel_path: Excel输出路径
    """
    # 获取两个目录的子文件夹名称
    print("正在获取原始数据目录的子文件夹...")
    original_folders = get_subfolder_names(original_dir)
    print(f"原始数据目录找到 {len(original_folders)} 个子文件夹")
    
    print("正在获取命名规范化目录的子文件夹...")
    normalized_folders = get_subfolder_names(normalized_dir)
    print(f"命名规范化目录找到 {len(normalized_folders)} 个子文件夹")
    
    # 找出在原始数据目录中存在但在命名规范化目录中不存在的子文件夹
    missing_folders = original_folders - normalized_folders
    
    print(f"\n对比结果:")
    print(f"原始数据目录子文件夹总数: {len(original_folders)}")
    print(f"命名规范化目录子文件夹总数: {len(normalized_folders)}")
    print(f"缺失的子文件夹数量: {len(missing_folders)}")
    
    if missing_folders:
        print("\n缺失的子文件夹列表:")
        for i, folder in enumerate(sorted(missing_folders), 1):
            print(f"{i}. {folder}")
        
        # 创建DataFrame
        df = pd.DataFrame({
            '缺失的子文件夹名称': sorted(missing_folders),
            '原始数据目录路径': original_dir,
            '命名规范化目录路径': normalized_dir,
            '状态': '未找到'
        })
        
        # 确保输出目录存在
        output_dir = Path(output_excel_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存到Excel
        try:
            df.to_excel(output_excel_path, index=False, engine='openpyxl')
            print(f"\n已保存缺失子文件夹列表到: {output_excel_path}")
            
            # 创建详细版本（包含所有文件夹信息）
            detailed_excel_path = output_excel_path.replace('.xlsx', '_detailed.xlsx')
            detailed_data = []
            
            # 添加所有原始文件夹信息
            for folder in sorted(original_folders):
                status = "存在" if folder in normalized_folders else "缺失"
                detailed_data.append({
                    '子文件夹名称': folder,
                    '状态': status,
                    '原始数据目录': "是",
                    '命名规范化目录': "是" if status == "存在" else "否"
                })
            
            # 添加只在规范化目录中存在的文件夹
            extra_folders = normalized_folders - original_folders
            for folder in sorted(extra_folders):
                detailed_data.append({
                    '子文件夹名称': folder,
                    '状态': "额外",
                    '原始数据目录': "否",
                    '命名规范化目录': "是"
                })
            
            detailed_df = pd.DataFrame(detailed_data)
            detailed_df.to_excel(detailed_excel_path, index=False, engine='openpyxl')
            print(f"已保存详细对比结果到: {detailed_excel_path}")
            
        except Exception as e:
            print(f"保存Excel文件时出错: {e}")
            return False
        
        return True
    else:
        print("\n恭喜！命名规范化目录包含了原始数据目录的所有子文件夹")
        
        # 检查是否有额外的文件夹
        extra_folders = normalized_folders - original_folders
        if extra_folders:
            print(f"\n注意：命名规范化目录中有 {len(extra_folders)} 个额外的子文件夹:")
            for folder in sorted(extra_folders):
                print(f"  - {folder}")
            
            # 保存额外文件夹信息
            extra_df = pd.DataFrame({
                '额外的子文件夹名称': sorted(extra_folders),
                '说明': '在命名规范化目录中存在但在原始数据目录中不存在'
            })
            
            extra_excel_path = output_excel_path.replace('.xlsx', '_extra.xlsx')
            extra_df.to_excel(extra_excel_path, index=False, engine='openpyxl')
            print(f"已保存额外文件夹列表到: {extra_excel_path}")
        
        return True


def main():
    # 设置目录路径
    original_data_dir = "/media/dell/T7 Shield/nnunet/AllData/珠江医院/原始数据"
    normalized_dir = "/media/dell/T7 Shield/nnunet/AllData/珠江医院/命名规范化"
    output_excel_path = "/media/dell/T7 Shield/nnunet/AllData/珠江医院/missing_folders_comparison.xlsx"
    
    print("开始对比子文件夹命名...")
    print("=" * 60)
    print(f"原始数据目录: {original_data_dir}")
    print(f"命名规范化目录: {normalized_dir}")
    print(f"输出Excel文件: {output_excel_path}")
    print("=" * 60)
    
    # 执行对比并导出到Excel
    success = compare_folders_and_export_to_excel(
        original_data_dir, 
        normalized_dir, 
        output_excel_path
    )
    
    if success:
        print("\n操作完成！")
    else:
        print("\n操作过程中出现错误！")


if __name__ == "__main__":
    main()