"""
缓存管理模块，用于管理所有处理器的缓存
"""

# 存储所有注册的缓存清理函数
_cache_cleaners = {}

def register_cache_cleaner(module_name, cleaner_func):
    """
    注册一个缓存清理函数
    
    Args:
        module_name (str): 模块名称
        cleaner_func (callable): 清理缓存的函数
    """
    _cache_cleaners[module_name] = cleaner_func

def clear_all_caches():
    """
    清理所有已注册的缓存
    """
    for module_name, cleaner_func in _cache_cleaners.items():
        try:
            cleaner_func()
            print(f"已清理 {module_name} 的缓存")
        except Exception as e:
            print(f"清理 {module_name} 缓存时出错: {str(e)}")

def clear_cache(module_name):
    """
    清理指定模块的缓存
    
    Args:
        module_name (str): 要清理缓存的模块名称
    """
    if module_name in _cache_cleaners:
        try:
            _cache_cleaners[module_name]()
            print(f"已清理 {module_name} 的缓存")
        except Exception as e:
            print(f"清理 {module_name} 缓存时出错: {str(e)}")
    else:
        print(f"未找到 {module_name} 的缓存清理函数") 