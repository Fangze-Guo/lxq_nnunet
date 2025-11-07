import os
import re
from pypinyin import lazy_pinyin, Style

def chinese_to_english(filename):
    """将文件名中的中文转换为拼音，保留原有数字和英文"""
    # 分离文件名和扩展名
    base, ext = os.path.splitext(filename)
    
    # 将中文部分转换为拼音
    def replace_chinese(match):
        chinese = match.group()
        return '_'.join(lazy_pinyin(chinese, style=Style.NORMAL))
    
    # 只转换中文部分，保留其他字符
    english_base = re.sub(r'[\u4e00-\u9fff]+', replace_chinese, base)
    
    # 清理特殊字符（只保留字母数字和下划线）
    english_base = re.sub(r'[^a-zA-Z0-9_]', '', english_base)
    
    # 处理连续的下划线
    english_base = re.sub(r'_+', '_', english_base).strip('_')
    
    # 如果结果为空则使用默认名
    if not english_base:
        english_base = 'dicom'
    
    return f"{english_base}{ext.lower()}"

def rename_dcm_files(root_dir):
    """递归重命名所有二级子文件夹中的DCM文件"""
    for first_level in os.listdir(root_dir):
        first_level_path = os.path.join(root_dir, first_level)
        
        if not os.path.isdir(first_level_path):
            continue
            
        print(f"\n处理一级文件夹: {first_level}")
        
        for second_level in os.listdir(first_level_path):
            second_level_path = os.path.join(first_level_path, second_level)
            
            if not os.path.isdir(second_level_path):
                continue
                
            print(f"  正在处理二级文件夹: {second_level}")
            renamed_count = 0
            
            for filename in os.listdir(second_level_path):
                if not filename.lower().endswith('.dcm'):
                    continue
                    
                old_path = os.path.join(second_level_path, filename)
                new_name = chinese_to_english(filename)
                new_path = os.path.join(second_level_path, new_name)
                
                # 处理文件名冲突
                counter = 1
                while os.path.exists(new_path):
                    base, ext = os.path.splitext(new_name)
                    new_name = f"{base}_{counter}{ext}"
                    new_path = os.path.join(second_level_path, new_name)
                    counter += 1
                
                os.rename(old_path, new_path)
                renamed_count += 1
                print(f"    {filename} -> {new_name}")
            
            print(f"  完成: 重命名了 {renamed_count} 个文件")

if __name__ == "__main__":
    # 安装依赖: pip install pypinyin
    input_dir = "/media/cqc/新加卷/my_data/HK/蒙片选取"
    
    print("=== 开始DCM文件重命名 ===")
    rename_dcm_files(input_dir)
    print("=== 重命名完成 ===")