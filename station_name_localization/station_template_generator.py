import json
import re
from typing import Dict, List, Tuple

def load_json_file(file_path: str) -> dict:
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_word_combinations(text: str) -> List[str]:
    """生成给定文本的所有可能词组组合"""
    words = text.split()
    combinations = []
    
    # 生成所有可能的连续词组
    for i in range(len(words)):
        for j in range(i + 1, len(words) + 1):
            combination = ' '.join(words[i:j])
            combinations.append(combination)
    
    # 按长度降序排序，这样我们会先匹配最长的词组
    combinations.sort(key=len, reverse=True)
    return combinations

def find_template_id(text: str, localization_data: Dict) -> Tuple[str, int]:
    """查找文本在本地化数据中的模板ID"""
    matching_ids = []
    for id_str, translations in localization_data.items():
        if translations.get('en') == text:
            matching_ids.append(int(id_str))
    
    if matching_ids:
        # 如果有多个匹配，返回ID最小的
        return str(min(matching_ids)), min(matching_ids)
    return None, None

def process_station_name(station_name: str, localization_data: Dict) -> str:
    """处理单个空间站名称，返回模板格式"""
    # 保存已经替换的部分，避免重复替换
    replaced_parts = {}
    template = station_name
    
    # 处理特殊模式（罗马数字和Moon后的数字）
    # 1. 处理独立的罗马数字（前后有空格的）
    roman_numerals = re.findall(r' ([IVX]+) ', station_name)
    for numeral in roman_numerals:
        # 罗马数字保持原样
        continue
        
    # 2. 处理"Moon"后面的数字
    moon_numbers = re.findall(r'Moon (\d+)', station_name)
    for number in moon_numbers:
        # 数字保持原样
        continue
    
    # 处理其他文本部分
    # 移除已知的特殊部分（罗马数字和Moon数字）后再处理其他文本
    remaining_text = station_name
    for part in remaining_text.split(' - '):
        combinations = generate_word_combinations(part.strip())
        for combo in combinations:
            if combo in replaced_parts:
                continue
                
            template_id, _ = find_template_id(combo, localization_data)
            if template_id:
                # 替换模板中的文本
                template = template.replace(combo, f"{{{template_id}}}")
                replaced_parts[combo] = template_id
                break
    
    return template

def main():
    # 加载数据文件
    stations_data = load_json_file('../accounting_entry_types/static_data/stations_202504102216.json')
    localization_data = load_json_file('../accounting_entry_types/output/combined_localization.json')

    # 存储结果的字典
    templates = {}
    
    # 处理每个空间站
    for station in stations_data['stations']:
        station_id = station['stationID']
        station_name = station['stationName']
        template = process_station_name(station_name, localization_data)
        templates[station_id] = template
    
    # 保存结果
    with open('station_name_templates.json', 'w', encoding='utf-8') as f:
        json.dump(templates, f, indent=2, ensure_ascii=False)

if __name__ == '__main__':
    main() 