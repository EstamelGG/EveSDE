import os
import platform
from pathlib import Path

def get_eve_shared_cache_path():
    """
    获取EVE Online的SharedCache目录路径
    
    在Windows上，从注册表获取路径
    在macOS上，使用固定的路径
    
    Returns:
        str: SharedCache目录的完整路径，如果无法获取则返回None
    """
    system = platform.system()
    
    if system == "Windows":
        import winreg
        try:
            # 尝试从注册表获取路径
            # 首先尝试当前用户的注册表
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\CCP\EVEONLINE", 0, winreg.KEY_READ)
                cache_path = winreg.QueryValueEx(key, "CACHEFOLDER")[0]
                winreg.CloseKey(key)
                return cache_path
            except (WindowsError, FileNotFoundError):
                # 如果当前用户注册表没有，尝试从所有用户的注册表获取
                try:
                    # 使用win32security获取当前用户的SID
                    import win32security
                    import win32api
                    import win32con
                    
                    # 获取当前用户的令牌
                    token = win32security.OpenProcessToken(
                        win32api.GetCurrentProcess(),
                        win32con.TOKEN_QUERY
                    )
                    
                    # 从令牌中获取用户SID
                    sid = win32security.GetTokenInformation(token, win32security.TokenUser)[0]
                    
                    # 将SID转换为字符串格式
                    sid_string = win32security.ConvertSidToStringSid(sid)
                    
                    # 使用SID构建注册表路径
                    key = winreg.OpenKey(winreg.HKEY_USERS, f"{sid_string}\\Software\\CCP\\EVEONLINE", 0, winreg.KEY_READ)
                    cache_path = winreg.QueryValueEx(key, "CACHEFOLDER")[0]
                    winreg.CloseKey(key)
                    print(f"EVE SharedCache路径: {cache_path}")
                    return cache_path
                except Exception as e:
                    print(f"无法从注册表获取EVE缓存路径: {e}")
            
            # 如果注册表方法失败，尝试默认路径
            default_path = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'CCP', 'EVE', 'SharedCache')
            if os.path.exists(default_path):
                print(f"EVE SharedCache路径: {default_path}")
                return default_path
                
        except Exception as e:
            print(f"获取Windows上的EVE缓存路径时出错: {e}")
            return None
            
    elif system == "Darwin":  # macOS
        # 在macOS上使用固定路径
        home = str(Path.home())
        cache_path = os.path.join(home, 'Library', 'Application Support', 'EVE Online', 'SharedCache')
        if os.path.exists(cache_path):
            print(f"EVE SharedCache路径: {cache_path}")
            return cache_path
        else:
            print("%s not exist." % cache_path)
            
    elif system == "Linux":
        # 在Linux上使用固定路径
        home = str(Path.home())
        cache_path = os.path.join(home, '.local', 'share', 'CCP', 'EVE', 'SharedCache')
        if os.path.exists(cache_path):
            print(f"EVE SharedCache路径: {cache_path}")
            return cache_path
        else:
            print("%s not exist." % cache_path)
    
    return None

def get_resfileindex():
    """
    获取EVE Online的resfileindex.txt文件路径
    
    检查SharedCache目录下的tq\resfileindex.txt文件是否存在
    
    Returns:
        str: resfileindex.txt文件的完整路径，如果文件不存在则返回None
    """
    # 获取SharedCache目录路径
    cache_path = get_eve_shared_cache_path()
    if not cache_path:
        print("无法获取EVE SharedCache路径")
        return None
    print(f"EVE SharedCache路径: {cache_path}")
    # 构建resfileindex.txt的完整路径
    system = platform.system()
    if system == "Windows":
        resfileindex_path = os.path.join(cache_path, 'tq', 'resfileindex.txt')
    elif system == "Darwin":  # macOS
        resfileindex_path = os.path.join(cache_path, 'tq', 'EVE.app', 'Contents', 'Resources', 'build', 'resfileindex.txt')
    else:
        resfileindex_path = os.path.join(cache_path, 'tq', 'resfileindex.txt')
    # 检查文件是否存在
    if os.path.exists(resfileindex_path):
        return resfileindex_path
    else:
        print(f"resfileindex.txt文件不存在: {resfileindex_path}")
        return None

# 使用示例
if __name__ == "__main__":
    cache_path = get_eve_shared_cache_path()
    if cache_path:
        print(f"EVE SharedCache路径: {cache_path}")
        
        resfileindex_path = get_resfileindex()
        if resfileindex_path:
            print(f"resfileindex.txt路径: {resfileindex_path}")
        else:
            print("无法获取resfileindex.txt路径")
    else:
        print("无法获取EVE SharedCache路径")
