#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对比两个文件夹中nii.gz文件的切片数量，只输出不相同的
"""

import os
import nibabel as nib
from pathlib import Path

def compare_slice_counts_simple(folder1, folder2):
    """
    对比两个文件夹中nii.gz文件的切片数量，只输出不相同的
    """
    print(f"🔍 对比切片数量 - 只显示不相同的文件")
    print(f"📁 文件夹1: {folder1}")
    print(f"📁 文件夹2: {folder2}")
    print("-" * 50)
    
    # 获取两个文件夹中的nii.gz文件
    files1 = sorted([f for f in os.listdir(folder1) if f.endswith('.nii.gz')])
    files2 = sorted([f for f in os.listdir(folder2) if f.endswith('.nii.gz')])
    
    # 找出共同的文件
    common_files = set(files1) & set(files2)
    
    print(f"📊 共同文件数量: {len(common_files)}")
    print(f"🔍 开始检查切片数量...\n")
    
    different_files = []
    
    for filename in sorted(common_files):
        file1_path = os.path.join(folder1, filename)
        file2_path = os.path.join(folder2, filename)
        
        try:
            # 加载文件1
            img1 = nib.load(file1_path)
            data1 = img1.get_fdata()
            slices1 = data1.shape[2]  # 第三维是切片维度
            
            # 加载文件2
            img2 = nib.load(file2_path)
            data2 = img2.get_fdata()
            slices2 = data2.shape[2]
            
            # 只记录不相同的
            if slices1 != slices2:
                different_files.append((filename, slices1, slices2))
                print(f"❌ {filename}")
                print(f"   文件夹1: {slices1} 个切片")
                print(f"   文件夹2: {slices2} 个切片")
                print(f"   🔄 差异: {abs(slices1 - slices2)} 个切片\n")
                
        except Exception as e:
            print(f"⚠️  处理文件 {filename} 时出错: {e}\n")
            different_files.append((filename, "ERROR", "ERROR"))
    
    # 总结
    print("=" * 50)
    if not different_files:
        print(f"✅ 所有 {len(common_files)} 个文件的切片数量都相同！")
    else:
        print(f"📊 总结: {len(different_files)} 个文件的切片数量不同")
        print(f"✅ {len(common_files) - len(different_files)} 个文件的切片数量相同")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="对比两个文件夹中nii.gz文件的切片数量")
    parser.add_argument("folder1", help="第一个文件夹路径")
    parser.add_argument("folder2", help="第二个文件夹路径")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.folder1):
        print(f"❌ 文件夹1不存在: {args.folder1}")
        exit(1)
        
    if not os.path.exists(args.folder2):
        print(f"❌ 文件夹2不存在: {args.folder2}")
        exit(1)
    
    compare_slice_counts_simple(args.folder1, args.folder2)