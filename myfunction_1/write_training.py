import os
import json
from pathlib import Path

def create_msd_json(task_dir):
    """
    为指定任务目录创建MSD格式的dataset.json文件
    目录结构:
    Task004_example/
    ├── imagesTr/    # 训练图像
    ├── imagesTs/    # 测试图像
    └── labelsTr/    # 训练标签
    """
    # 定义路径
    json_path = os.path.join(task_dir, "dataset.json")
    images_tr_dir = os.path.join(task_dir, "imagesTr")
    images_ts_dir = os.path.join(task_dir, "imagesTs")
    labels_tr_dir = os.path.join(task_dir, "labelsTr")

    # 验证目录存在
    for d in [images_tr_dir, images_ts_dir, labels_tr_dir]:
        if not os.path.exists(d):
            raise FileNotFoundError(f"Required directory missing: {d}")

    # 获取文件列表（确保排序一致性）
    train_images = sorted([f for f in os.listdir(images_tr_dir) if f.endswith('.nii.gz')])
    test_images = sorted([f for f in os.listdir(images_ts_dir) if f.endswith('.nii.gz')])
    train_labels = sorted([f for f in os.listdir(labels_tr_dir) if f.endswith('.nii.gz')])

    # 创建MSD格式数据
    msd_data = {
        "name": Path(task_dir).name,
        "description": "Automatically generated MSD-format dataset",
        "reference": "Generated from nnUNet raw data",
        "licence": "CC-BY-SA 4.0",
        "release": "1.0",
        "modality": {"0": "CT"},  # 修改为实际模态
        "labels": {               # 修改为实际标签
            "0": "background",
            "1": "tumor"
        },
        "numTraining": len(train_images),
        "numTest": len(test_images),
        "training": [],
        "test": []
    }

    # 构建training列表（确保图像和标签匹配）
    for img in train_images:
        label = img  # 假设同名
        if label in train_labels:
            msd_data["training"].append({
                "image": f"./imagesTr/{img}",
                "label": f"./labelsTr/{label}"
            })
        else:
            print(f"Warning: Missing label for {img}")

    # 构建test列表
    msd_data["test"] = [f"./imagesTs/{f}" for f in test_images]

    # 写入JSON文件
    with open(json_path, 'w') as f:
        json.dump(msd_data, f, indent=2, ensure_ascii=False)

    print(f"Successfully created MSD-format dataset.json at {json_path}")
    print(f"Training cases: {len(msd_data['training'])}")
    print(f"Test cases: {len(msd_data['test'])}")

if __name__ == "__main__":
    # 修改为您的实际路径
    task_path = "/home/cqc/下载/nnUNet-master/DATASET/nnUNet_raw/Task004_example"
    
    # 验证路径存在
    if not os.path.exists(task_path):
        raise FileNotFoundError(f"Task directory not found: {task_path}")
    
    create_msd_json(task_path)