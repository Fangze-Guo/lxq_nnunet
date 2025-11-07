import os

def compare_folders(dir1, dir2):
    # 获取目录1的子文件夹
    folders1 = set([f for f in os.listdir(dir1) if os.path.isdir(os.path.join(dir1, f))])
    # 获取目录2的子文件夹
    folders2 = set([f for f in os.listdir(dir2) if os.path.isdir(os.path.join(dir2, f))])
    
    print(f"precontrast目录子文件夹数量: {len(folders1)}")
    print(f"HBP目录子文件夹数量: {len(folders2)}")
    print()
    
    # 找出只在precontrast中的文件夹
    only_in_precontrast = folders1 - folders2
    if only_in_precontrast:
        print("只在precontrast中的文件夹:")
        for folder in sorted(only_in_precontrast):
            print(f"  - {folder}")
    else:
        print("没有只在precontrast中的文件夹")
    print()
    
    # 找出只在HBP中的文件夹
    only_in_hbp = folders2 - folders1
    if only_in_hbp:
        print("只在HBP中的文件夹:")
        for folder in sorted(only_in_hbp):
            print(f"  - {folder}")
    else:
        print("没有只在HBP中的文件夹")
    print()
    
    # 共同的文件夹
    common_folders = folders1 & folders2
    print(f"共同文件夹数量: {len(common_folders)}")
    if common_folders:
        print("共同文件夹示例 (前10个):")
        for folder in sorted(list(common_folders)[:10]):
            print(f"  - {folder}")

# 使用您的路径
dir1 = "/media/dell/T7 Shield/nnunet/AllData/ST/finished/precontrast/precontrast_dicom"
dir2 = "/media/dell/T7 Shield/nnunet/AllData/ST/finished/HBP/HBP_dicom"
compare_folders(dir1, dir2)