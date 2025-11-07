import os
import shutil
import time
from tqdm import tqdm

def get_subfolders(src_folder):
    """获取所有子文件夹列表"""
    return [f for f in os.listdir(src_folder) 
            if os.path.isdir(os.path.join(src_folder, f))]

def calculate_batch_size(src_folder, batch):
    """计算当前批次（2个文件夹）的总文件大小"""
    total_size = 0
    for folder in batch:
        folder_path = os.path.join(src_folder, folder)
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                try:
                    total_size += os.path.getsize(os.path.join(root, file))
                except:
                    continue
    return total_size

def copy_with_speed_limit(src, dst, speed_limit_kbps=1024, pbar=None):
    """复制单个文件，并限制速度"""
    chunk_size = 1024 * 32  # 32KB
    delay = (chunk_size / 1024) / speed_limit_kbps  # 控制速度的延迟
    
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    
    try:
        file_size = os.path.getsize(src)
        with open(src, 'rb') as fsrc, open(dst, 'wb') as fdst:
            while True:
                buf = fsrc.read(chunk_size)
                if not buf:
                    break
                fdst.write(buf)
                if pbar:
                    pbar.update(len(buf))
                time.sleep(delay)
        return True
    except Exception as e:
        print(f"\n复制 {src} 出错: {e}")
        return False

def copy_batch(src_folder, dst_folder, batch, speed_limit_kbps=1024):
    """复制一批（2个）子文件夹"""
    batch_size = calculate_batch_size(src_folder, batch)
    print(f"\n正在复制: {', '.join(batch)} | 总大小: {batch_size/1024/1024:.2f} MB")
    
    with tqdm(total=batch_size, unit='B', unit_scale=True, 
             desc="当前进度", leave=False) as pbar:
        for folder in batch:
            src_path = os.path.join(src_folder, folder)
            dst_path = os.path.join(dst_folder, folder)
            
            if os.path.exists(dst_path):
                print(f"目标文件夹 {dst_path} 已存在，跳过")
                continue
            
            print(f"开始复制: {folder}")
            start_time = time.time()
            
            shutil.copytree(src_path, dst_path,
                          copy_function=lambda s, d: copy_with_speed_limit(s, d, speed_limit_kbps, pbar))
            
            elapsed = time.time() - start_time
            print(f"完成 {folder} | 耗时: {elapsed:.2f}秒")

def main():
    # 源文件夹和目标文件夹
    source_folder = "/media/cqc/萱君的外地磁盘/GDPH160"
    destination_folder = "/media/cqc/新加卷/my_data/广东省人民医院/GPDH"
    
    # 参数设置
    speed_limit = 1024  # 传输速度限制 (Kbps)
    batch_size = 2      # 每轮复制的文件夹数
    
    # 获取所有子文件夹
    subfolders = get_subfolders(source_folder)
    total = len(subfolders)
    
    if total == 0:
        print("源文件夹中没有子文件夹!")
        return
    
    print(f"开始复制 {total} 个子文件夹 (每轮 {batch_size} 个)...")
    overall_start = time.time()
    
    # 分批处理
    for i in range(0, total, batch_size):
        batch = subfolders[i:i+batch_size]
        print(f"\n=== 第 {i//batch_size + 1} 轮 ===")
        
        copy_batch(source_folder, destination_folder, batch, speed_limit)
        
        # 如果不是最后一批，添加间隔
        if i + batch_size < total:
            print("\n等待下一轮...")
            time.sleep(1)
    
    total_time = time.time() - overall_start
    print(f"\n所有文件夹复制完成! 总耗时: {total_time:.2f}秒")

if __name__ == "__main__":
    try:
        from tqdm import tqdm
    except ImportError:
        print("正在安装tqdm库...")
        import subprocess
        subprocess.check_call(["python", "-m", "pip", "install", "tqdm"])
        from tqdm import tqdm
    
    main()