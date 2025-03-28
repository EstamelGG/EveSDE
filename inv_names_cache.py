import yaml

# 全局变量来存储 invNames 数据
_inv_names_cache = None

def read_invnames_yaml(file_path):
    """读取 invNames.yaml 文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def get_inv_names(invnames_file_path):
    """
    读取并缓存 invNames.yaml 文件中的数据。
    返回一个字典，其中 key 为 itemID，value 为 itemName。
    """
    global _inv_names_cache
    
    # 如果缓存中已有数据，直接返回
    if _inv_names_cache is not None:
        return _inv_names_cache
    
    # 读取 invNames.yaml 文件
    data = read_invnames_yaml(invnames_file_path)
    
    # 创建 itemID 到 itemName 的映射
    _inv_names_cache = {str(item_id): name for item_id, name in data.items()}
    
    return _inv_names_cache 