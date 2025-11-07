import numpy as np
import torch

# 测试NumPy到PyTorch的转换
data = np.random.rand(10, 10)
tensor_data = torch.from_numpy(data)
print("转换成功！")
print(f"NumPy数组形状: {data.shape}")
print(f"PyTorch张量形状: {tensor_data.shape}")