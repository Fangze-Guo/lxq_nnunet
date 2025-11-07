import torch
print(torch.cuda.is_available())  # 检查 CUDA 是否可用
print(torch.cuda.device_count())  # 查看有多少个 GPU 可用
print(torch.cuda.get_device_name(0))  # 如果有多个 GPU，查看第一个 GPU 名字
