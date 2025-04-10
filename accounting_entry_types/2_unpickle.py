import os
import pickle
import json
import shutil

def unpickle_localization_files():
    """
    解包raw目录中的本地化pickle文件到extra目录
    
    从./raw目录读取所有localization_fsd_*.pickle文件，
    解包它们并将结果保存到./extra目录中
    
    Returns:
        dict: 语言代码到解包后数据结构的映射
    """
    # 定义目录路径
    raw_dir = "./raw"
    extra_dir = "./extra"
    output_dir = "./output"

    # 检查raw目录是否存在
    if not os.path.exists(raw_dir):
        print(f"错误: raw目录不存在: {raw_dir}")
        return {}
    
    # 如果extra目录存在，则先删除
    if os.path.exists(extra_dir):
        try:
            shutil.rmtree(extra_dir)
            print(f"已删除现有的extra目录: {extra_dir}")
        except Exception as e:
            print(f"删除extra目录时出错: {e}")
            return {}

    # 如果output目录存在，则先删除
    if os.path.exists(output_dir):
        try:
            shutil.rmtree(output_dir)
            print(f"已删除现有的output目录: {output_dir}")
        except Exception as e:
            print(f"删除output目录时出错: {e}")
            return {}

    # 创建extra目录
    os.makedirs(extra_dir, exist_ok=True)
    print(f"已创建extra目录: {extra_dir}")
    os.makedirs(output_dir, exist_ok=True)
    print(f"已创建output目录: {output_dir}")
    
    # 存储解包结果的字典
    result = {}
    
    # 获取raw目录中的所有pickle文件
    pickle_files = [f for f in os.listdir(raw_dir) if f.startswith("localization_fsd_") and f.endswith(".pickle")]
    
    if not pickle_files:
        print(f"错误: 在{raw_dir}目录中没有找到本地化pickle文件")
        return {}
    
    # 解包每个pickle文件
    for pickle_file in pickle_files:
        # 从文件名中提取语言代码
        lang_code = pickle_file.replace("localization_fsd_", "").replace(".pickle", "")
        
        # 构建完整的pickle文件路径
        pickle_path = os.path.join(raw_dir, pickle_file)
        
        try:
            # 解包pickle文件
            with open(pickle_path, 'rb') as f:
                data = pickle.load(f)
            
            # 提取语言代码和本地化数据
            file_lang_code, translations = data
            
            # 将本地化数据转换为更易读的格式
            processed_data = {}
            for msg_id, msg_tuple in translations.items():
                text, meta1, meta2 = msg_tuple
                processed_data[str(msg_id)] = {
                    "text": text,
                    "metadata": {
                        "meta1": meta1,
                        "meta2": meta2
                    }
                }
            
            # 为每种语言创建一个子目录
            lang_dir = os.path.join(extra_dir, lang_code)
            os.makedirs(lang_dir, exist_ok=True)
            
            # 保存为JSON格式（更易读）
            json_file = os.path.join(lang_dir, f"{lang_code}_localization.json")
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(processed_data, f, ensure_ascii=False, indent=2)
            
            # 同时保存原始pickle格式（以防需要）
            pickle_output = os.path.join(lang_dir, f"{lang_code}_localization.pkl")
            with open(pickle_output, 'wb') as f:
                pickle.dump(processed_data, f)
            
            print(f"已解包: {pickle_file} -> {lang_dir}")
            result[lang_code] = processed_data
            
        except Exception as e:
            print(f"解包文件时出错 {pickle_file}: {e}")
    
    return result

def analyze_localization_data(unpickled_data):
    """
    分析解包后的本地化数据结构
    
    Args:
        unpickled_data: 解包后的本地化数据
    
    Returns:
        dict: 包含分析结果的字典
    """
    if not unpickled_data:
        return {"error": "没有数据可分析"}
    
    analysis = {}
    
    # 分析每种语言的数据
    for lang_code, data in unpickled_data.items():
        lang_analysis = {
            "消息数量": len(data),
            "示例消息": {}
        }
        
        # 获取前5个消息作为示例
        for msg_id in list(data.keys())[:5]:
            lang_analysis["示例消息"][msg_id] = data[msg_id]["text"]
        
        # 计算文本长度统计
        text_lengths = [len(msg["text"]) for msg in data.values() if msg["text"]]
        if text_lengths:
            lang_analysis["文本长度统计"] = {
                "最短": min(text_lengths),
                "最长": max(text_lengths),
                "平均": sum(text_lengths) / len(text_lengths)
            }
        
        # 检查空值或None值的数量
        empty_count = sum(1 for msg in data.values() if not msg["text"])
        lang_analysis["空文本数量"] = empty_count
        
        analysis[lang_code] = lang_analysis
    
    return analysis

# 使用示例
if __name__ == "__main__":
    print("开始解包本地化pickle文件...")
    unpickled_data = unpickle_localization_files()
    
    if unpickled_data:
        print(f"\n成功解包了 {len(unpickled_data)} 个本地化文件到extra目录")
        
        # 分析解包后的数据
        print("\n分析解包后的数据结构:")
        analysis = analyze_localization_data(unpickled_data)
        
        for lang_code, lang_analysis in analysis.items():
            print(f"\n语言: {lang_code}")
            print("  消息数量:", lang_analysis["消息数量"])
            print("  空文本数量:", lang_analysis["空文本数量"])
            if "文本长度统计" in lang_analysis:
                stats = lang_analysis["文本长度统计"]
                print(f"  文本长度: 最短={stats['最短']}, 最长={stats['最长']}, 平均={stats['平均']:.2f}")
            print("\n  示例消息:")
            for msg_id, text in lang_analysis["示例消息"].items():
                print(f"    {msg_id}: {text}")
    else:
        print("解包文件失败") 