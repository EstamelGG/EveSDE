import os
import re
import shutil
from get_path import get_resfileindex, get_eve_shared_cache_path

def get_localization_pickles():
    """
    从resfileindex.txt文件中搜索本地化pickle文件的信息
    
    搜索格式为：localization_fsd_[\w-]+.pickle的文件
    例如：res:/localizationfsd/localization_fsd_de.pickle,f7/f781e479bccfd00e_e5f6aabef27135480f0f326a2c708a3b,e5f6aabef27135480f0f326a2c708a3b,41925665,8268032
    
    返回一个字典，键为语言代码（如'de'），值为完整的pickle文件路径
    排除语言代码为"main"的情况
    
    Returns:
        dict: 语言代码到完整文件路径的映射，如果无法获取则返回空字典
    """
    # 获取resfileindex.txt文件路径
    resfileindex_path = get_resfileindex()
    if not resfileindex_path:
        print("无法获取resfileindex.txt文件路径")
        return {}
    
    # 获取SharedCache目录路径
    cache_path = get_eve_shared_cache_path()
    if not cache_path:
        print("无法获取EVE SharedCache路径")
        return {}
    
    # 正则表达式模式，匹配localization_fsd_[\w-]+.pickle格式的文件
    pattern = r'res:/localizationfsd/localization_fsd_([\w-]+)\.pickle,([^,]+)'
    
    # 存储结果的字典
    result = {}
    
    try:
        # 读取resfileindex.txt文件
        with open(resfileindex_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 查找所有匹配项
        matches = re.findall(pattern, content)
        
        # 处理匹配结果，排除语言代码为"main"的情况
        for lang_code, file_path in matches:
            if lang_code.lower() != "main":  # 排除"main"语言
                # 构建完整的pickle文件路径
                full_path = os.path.join(cache_path, 'ResFiles', file_path)
                
                # 检查文件是否存在
                if os.path.exists(full_path):
                    if lang_code == "en-us":
                        lang_code = "en"
                    result[lang_code] = full_path
                else:
                    print(f"警告: 本地化pickle文件不存在: {full_path}")
        
        return result
    
    except Exception as e:
        print(f"处理resfileindex.txt文件时出错: {e}")
        return {}

def copy_localization_pickles_to_raw():
    """
    将本地化pickle文件复制到项目的raw目录
    
    从EVE SharedCache中获取本地化pickle文件，并将它们复制到当前项目路径下的raw目录
    文件将被重命名为localization_fsd_xx.pickle格式，其中xx是语言代码
    
    Returns:
        dict: 语言代码到目标文件路径的映射
    """
    # 获取本地化pickle文件
    localization_pickles = get_localization_pickles()
    if not localization_pickles:
        print("未找到本地化pickle文件")
        return {}
    
    raw_dir = "./raw"
    
    # 如果raw目录存在，则先删除
    if os.path.exists(raw_dir):
        try:
            shutil.rmtree(raw_dir)
            print(f"已删除现有的raw目录: {raw_dir}")
        except Exception as e:
            print(f"删除raw目录时出错: {e}")
            return {}
    
    # 创建raw目录
    os.makedirs(raw_dir, exist_ok=True)
    print(f"已创建raw目录: {raw_dir}")
    
    # 存储复制结果的字典
    result = {}
    
    # 复制每个pickle文件到raw目录
    for lang_code, source_path in localization_pickles.items():
        # 构建目标文件路径
        target_filename = f"localization_fsd_{lang_code}.pickle"
        target_path = os.path.join(raw_dir, target_filename)
        
        try:
            # 复制文件
            shutil.copy2(source_path, target_path)
            print(f"已复制: {source_path} -> {target_path}")
            result[lang_code] = target_path
        except Exception as e:
            print(f"复制文件时出错 {source_path} -> {target_path}: {e}")
    
    return result

# 使用示例
if __name__ == "__main__":
    localization_pickles = get_localization_pickles()
    
    if localization_pickles:
        print("找到以下本地化pickle文件:")
        for lang_code, file_path in localization_pickles.items():
            print(f"语言: {lang_code}, 文件路径: {file_path}")
        
        # 复制文件到raw目录
        print("\n开始复制文件到raw目录...")
        copied_files = copy_localization_pickles_to_raw()
        if copied_files:
            print(f"\n成功复制了 {len(copied_files)} 个本地化pickle文件到raw目录")
        else:
            print("复制文件失败")
    else:
        print("未找到本地化pickle文件或处理出错") 