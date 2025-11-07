import os
import shutil
from pathlib import Path

def copy_folders_based_on_files(source_base, target_base, reference_dir, file_extensions=None):
    """
    根据参考目录中的文件名，从源目录复制对应的文件夹到目标目录
    
    参数:
        source_base: 源文件夹基础路径
        target_base: 目标文件夹基础路径  
        reference_dir: 参考目录，包含要复制的文件名
        file_extensions: 支持的文件扩展名列表，默认为 ['.nii.gz', '.nii']
    """
    
    # 设置默认文件扩展名
    if file_extensions is None:
        file_extensions = ['.nii.gz', '.nii']
    
    # 检查目录是否存在
    if not os.path.exists(source_base):
        print(f"❌ 源目录不存在: {source_base}")
        return
    
    if not os.path.exists(reference_dir):
        print(f"❌ 参考目录不存在: {reference_dir}")
        return
    
    # 创建目标目录（如果不存在）
    os.makedirs(target_base, exist_ok=True)
    print(f"✅ 目标目录已创建/确认: {target_base}")
    
    # 获取参考目录中指定扩展名的文件
    try:
        # 获取所有文件
        all_files = os.listdir(reference_dir)
        
        # 筛选指定扩展名的文件
        matching_files = []
        for file in all_files:
            for ext in file_extensions:
                if file.endswith(ext):
                    matching_files.append(file)
                    break
        
        # 提取文件夹名（去掉扩展名）
        folder_names = []
        for file in matching_files:
            # 去掉扩展名
            folder_name = file
            for ext in file_extensions:
                if file.endswith(ext):
                    folder_name = file[:-len(ext)]
                    break
            folder_names.append(folder_name)
        
        print(f"📁 在参考目录中找到 {len(matching_files)} 个匹配文件")
        print(f"📋 支持的文件扩展名: {file_extensions}")
        print(f"📄 匹配文件列表: {matching_files}")
        print(f"📂 对应的文件夹名列表: {folder_names}")
        
    except Exception as e:
        print(f"❌ 读取参考目录失败: {e}")
        return
    
    # 统计变量
    success_count = 0
    skip_count = 0
    error_count = 0
    copied_folders = []
    missing_folders = []
    
    # 遍历文件夹名列表并复制
    for folder_name in folder_names:
        source_path = os.path.join(source_base, folder_name)
        target_path = os.path.join(target_base, folder_name)
        
        print(f"\n🔍 处理文件夹: {folder_name}")
        print(f"   源路径: {source_path}")
        print(f"   目标路径: {target_path}")
        
        # 检查源文件夹是否存在
        if not os.path.exists(source_path):
            print(f"   ⚠️ 源文件夹不存在，跳过: {source_path}")
            skip_count += 1
            missing_folders.append(folder_name)
            continue
        
        # 检查目标文件夹是否已存在
        if os.path.exists(target_path):
            print(f"   ⚠️ 目标文件夹已存在，跳过: {target_path}")
            skip_count += 1
            continue
        
        try:
            # 复制文件夹
            print(f"   📤 正在复制: {folder_name}")
            shutil.copytree(source_path, target_path)
            print(f"   ✅ 复制成功: {folder_name}")
            success_count += 1
            copied_folders.append(folder_name)
            
        except Exception as e:
            print(f"   ❌ 复制失败: {folder_name}, 错误: {e}")
            error_count += 1
    
    # 输出详细统计结果
    print(f"\n" + "="*60)
    print("📊 复制任务完成统计:")
    print("="*60)
    
    print(f"\n✅ 成功复制 ({success_count}):")
    for folder in copied_folders:
        print(f"   📁 {folder}")
    
    if missing_folders:
        print(f"\n❌ 缺失文件夹 ({len(missing_folders)}):")
        for folder in missing_folders:
            print(f"   📁 {folder}")
    
    print(f"\n📈 统计摘要:")
    print(f"   ✅ 成功复制: {success_count} 个文件夹")
    print(f"   ⚠️ 跳过: {skip_count} 个文件夹")
    print(f"   ❌ 失败: {error_count} 个文件夹")
    print(f"   📁 总计处理: {len(folder_names)} 个文件夹")
    print(f"   📄 参考文件: {len(matching_files)} 个")
    print("="*60)

def main():
    # 定义路径
    source_base = "/media/dell/T7 Shield/nnunet/AllData/ST/SDFY_100"
    target_base = "/media/dell/T7 Shield/nnunet/AllData/ST/ST_dicom/ST_new"
    reference_dir = "/media/dell/T7 Shield/nnunet/AllData/ST/precontrast_mask_nii/dicom_to_nii"
    
    # 支持的文件扩展名
    supported_extensions = ['.nii.gz', '.nii']  # 可以添加更多扩展名
    
    print("🚀 开始文件夹复制任务")
    print(f"📂 源目录: {source_base}")
    print(f"🎯 目标目录: {target_base}")
    print(f"📋 参考目录: {reference_dir}")
    print(f"📄 支持的文件类型: {supported_extensions}")
    print("-" * 60)
    
    # 执行复制任务
    copy_folders_based_on_files(source_base, target_base, reference_dir, supported_extensions)

if __name__ == "__main__":
    main()