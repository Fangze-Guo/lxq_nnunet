import os


def check_map_in_subfolders(root_path):
    """
    检查根路径下所有二级子文件夹名称是否包含"map"
    如果包含，则输出对应的一级子文件夹路径
    """
    result_folders = []

    # 遍历一级子文件夹
    for level1_folder in os.listdir(root_path):
        level1_path = os.path.join(root_path, level1_folder)

        # 确保是一级子文件夹（目录）
        if os.path.isdir(level1_path):
            # 遍历二级子文件夹
            for level2_folder in os.listdir(level1_path):
                level2_path = os.path.join(level1_path, level2_folder)

                # 确保是二级子文件夹（目录）
                if os.path.isdir(level2_path):
                    # 检查二级子文件夹名称是否包含"map"
                    if "map" in level2_folder.lower():
                        result_folders.append(level1_path)
                        break  # 找到一个就跳出内层循环

    return result_folders


def main():
    # 指定要检查的根路径
    root_path = "/media/dell/T7 Shield/nnunet/AllData/GXYF/分组数据/precontrast/4_组4_pre"

    # 检查路径是否存在
    if not os.path.exists(root_path):
        print(f"错误：路径不存在 - {root_path}")
        return

    # 获取包含"map"字段的二级子文件夹对应的一级子文件夹
    matching_folders = check_map_in_subfolders(root_path)

    # 输出结果
    if matching_folders:
        print("以下一级子文件夹包含名称中有'map'的二级子文件夹：")
        for folder in matching_folders:
            print(folder)
    else:
        print("未找到包含'map'字段的二级子文件夹")


if __name__ == "__main__":
    main()