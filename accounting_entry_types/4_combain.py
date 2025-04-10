#!/usr/bin/env python3
# -*- coding: utf-8 -*-


# 将输出的本地化字符串组合展示，同时提取出能够一一对应的英-中本地化对照


import json
import os
import glob
from collections import defaultdict

def load_json_file(file_path):
    """加载JSON文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"加载 {file_path} 时出错: {e}")
        return {}

def save_json_file(data, file_path):
    """保存JSON文件"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"成功保存到 {file_path}")
    except Exception as e:
        print(f"保存到 {file_path} 时出错: {e}")

def get_language_code(dir_path):
    """从目录路径中提取语言代码"""
    return os.path.basename(dir_path)

def main():
    # 获取基础目录
    base_dir = os.path.dirname(os.path.abspath(__file__))
    extra_dir = os.path.join(base_dir, "extra")
    
    # 获取所有语言目录
    language_dirs = [d for d in glob.glob(os.path.join(extra_dir, "*")) if os.path.isdir(d)]
    
    # 加载所有语言的本地化数据
    localization_data = {}
    for lang_dir in language_dirs:
        lang_code = get_language_code(lang_dir)
        json_file = os.path.join(lang_dir, f"{lang_code}_localization.json")
        if os.path.exists(json_file):
            localization_data[lang_code] = load_json_file(json_file)
            print(f"已加载 {lang_code} 的本地化数据")
    
    # 创建合并后的数据结构
    combined_data = {}
    
    # 获取所有ID
    all_ids = set()
    for lang_data in localization_data.values():
        all_ids.update(lang_data.keys())
    
    # 合并所有语言的文本
    for entry_id in all_ids:
        combined_data[entry_id] = {}
        
        # 从每种语言中获取文本
        for lang_code, lang_data in localization_data.items():
            if entry_id in lang_data:
                combined_data[entry_id][lang_code] = lang_data[entry_id]["text"]
    
    # 保存合并后的JSON文件
    output_file = os.path.join(base_dir, "output", "combined_localization.json")
    save_json_file(combined_data, output_file)
    
    print(f"合并完成！共处理了 {len(combined_data)} 个条目，包含 {len(localization_data)} 种语言。")
    
    # 创建英文到中文的映射
    en_to_zh = {}
    # 用于记录每个英文文本出现的次数
    en_count = {}
    
    # 遍历所有条目，统计每个英文文本出现的次数
    for entry_id, translations in combined_data.items():
        if "en" in translations and "zh" in translations:
            en_text = translations["en"]
            if en_text in en_count:
                en_count[en_text] += 1
            else:
                en_count[en_text] = 1
    
    # 只保留出现次数为1的英文文本对应的中文文本
    for entry_id, translations in combined_data.items():
        if "en" in translations and "zh" in translations:
            en_text = translations["en"]
            zh_text = translations["zh"]
            
            # 只有当英文文本只出现一次时，才添加到映射中
            if en_count[en_text] == 1:
                en_to_zh[en_text] = zh_text
    
    # 保存英文到中文的映射
    en_zh_file = os.path.join(base_dir, "output", "en_zh_mapping.json")
    save_json_file(en_to_zh, en_zh_file)
    
    print(f"英文到中文的映射完成！共处理了 {len(en_to_zh)} 个英文条目。")

if __name__ == "__main__":
    main() 