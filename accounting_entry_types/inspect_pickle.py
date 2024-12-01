import os
import pickle
import sys
from pprint import pprint

def inspect_pickle_file(pickle_path):
    """
    检查pickle文件的内容结构
    
    Args:
        pickle_path: pickle文件的路径
    
    Returns:
        dict: 包含pickle文件结构信息的字典
    """
    if not os.path.exists(pickle_path):
        print(f"错误: 文件不存在: {pickle_path}")
        return {}
    
    try:
        # 加载pickle文件
        with open(pickle_path, 'rb') as f:
            data = pickle.load(f)
        
        # 分析数据结构
        structure = {
            "类型": type(data).__name__,
            "大小": sys.getsizeof(data),
            "结构信息": {}
        }
        
        # 如果是字典，分析键和值
        if isinstance(data, dict):
            structure["结构信息"]["键数量"] = len(data)
            structure["结构信息"]["键类型"] = {k: type(v).__name__ for k, v in list(data.items())[:5]}
            
            # 检查是否有嵌套结构
            nested_structures = {}
            for key, value in list(data.items())[:5]:  # 只检查前5个键
                if isinstance(value, (dict, list)):
                    nested_structures[key] = {
                        "类型": type(value).__name__,
                        "大小": len(value) if hasattr(value, '__len__') else "N/A"
                    }
            
            if nested_structures:
                structure["结构信息"]["嵌套结构"] = nested_structures
        
        # 如果是列表，分析元素
        elif isinstance(data, list):
            structure["结构信息"]["元素数量"] = len(data)
            if data:
                structure["结构信息"]["元素类型"] = type(data[0]).__name__
                structure["结构信息"]["前5个元素"] = [type(item).__name__ for item in data[:5]]
        
        # 如果是其他类型，提供基本信息
        else:
            structure["结构信息"]["值"] = str(data)[:100] + "..." if len(str(data)) > 100 else str(data)
        
        return structure
    
    except Exception as e:
        print(f"检查pickle文件时出错: {e}")
        return {"错误": str(e)}

def inspect_raw_directory():
    """
    检查raw目录中的所有pickle文件
    
    Returns:
        dict: 文件名到结构信息的映射
    """
    raw_dir = "./raw"
    if not os.path.exists(raw_dir):
        print(f"错误: raw目录不存在: {raw_dir}")
        return {}
    
    # 获取所有pickle文件
    pickle_files = [f for f in os.listdir(raw_dir) if f.startswith("localization_fsd_") and f.endswith(".pickle")]
    
    if not pickle_files:
        print(f"错误: 在{raw_dir}目录中没有找到本地化pickle文件")
        return {}
    
    # 检查每个pickle文件
    results = {}
    for pickle_file in pickle_files:
        pickle_path = os.path.join(raw_dir, pickle_file)
        print(f"\n检查文件: {pickle_file}")
        
        # 检查文件大小
        file_size = os.path.getsize(pickle_path)
        print(f"文件大小: {file_size / 1024 / 1024:.2f} MB")
        
        # 检查pickle内容
        structure = inspect_pickle_file(pickle_path)
        results[pickle_file] = structure
        
        # 打印结构信息
        print("结构信息:")
        pprint(structure)
    
    return results

# 使用示例
if __name__ == "__main__":
    print("开始检查raw目录中的pickle文件...")
    results = inspect_raw_directory()
    
    if results:
        print(f"\n成功检查了 {len(results)} 个pickle文件")
    else:
        print("检查pickle文件失败") 