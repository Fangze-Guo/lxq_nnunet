import os
import shutil

def copy_folders_without_brackets(source_path, target_path):
    """
    复制源文件夹中所有不包含括号（包括中文和英文括号）的子文件夹到目标文件夹
    
    :param source_path: 源文件夹路径
    :param target_path: 目标文件夹路径
    """
    # 确保目标文件夹存在
    os.makedirs(target_path, exist_ok=True)
    
    # 定义要排除的括号类型（中文和英文括号）
    brackets = ['(', ')', '（', '）']
    
    # 遍历源文件夹中的所有项目
    for item in os.listdir(source_path):
        item_path = os.path.join(source_path, item)
        
        # 只处理子文件夹
        if os.path.isdir(item_path):
            # 检查文件夹名是否包含任何类型的括号
            has_brackets = any(bracket in item for bracket in brackets)
            
            if not has_brackets:
                target_item_path = os.path.join(target_path, item)
                
                # 如果目标文件夹已存在，先删除（可选）
                if os.path.exists(target_item_path):
                    shutil.rmtree(target_item_path)
                
                # 复制文件夹
                shutil.copytree(item_path, target_item_path)
                print(f"已复制: {item}")
            else:
                print(f"跳过（包含括号）: {item}")
        else:
            print(f"跳过（不是文件夹）: {item}")

# 使用示例
if __name__ == "__main__":
    source_dir = "/media/cqc/新加卷/my_data/SDYFY/SDYFY_100_pre"
    target_dir = "/media/cqc/新加卷/my_data/SDYFY/SDYFY_100_no_brackets"
    
    copy_folders_without_brackets(source_dir, target_dir)
    print("操作完成！")
    