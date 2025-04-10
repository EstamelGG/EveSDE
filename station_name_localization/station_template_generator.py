import json
import re
import logging
from typing import Dict, List, Tuple, Optional
from tqdm import tqdm
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,  # 改为DEBUG级别以显示更多信息
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'station_template_generator_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log', encoding='utf-8'),
    ]
)
logger = logging.getLogger(__name__)

class TemplateCache:
    def __init__(self):
        self.cache: Dict[str, Optional[Tuple[str, int]]] = {}
        self.hits = 0
        self.misses = 0
    
    def get(self, text: str) -> Optional[Tuple[str, int]]:
        """从缓存中获取模板ID"""
        if text in self.cache:
            self.hits += 1
            return self.cache[text]
        self.misses += 1
        return None
    
    def set(self, text: str, value: Optional[Tuple[str, int]]):
        """将模板ID存入缓存"""
        self.cache[text] = value
    
    def get_stats(self) -> Dict[str, int]:
        """获取缓存统计信息"""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        return {
            "hits": self.hits,
            "misses": self.misses,
            "total": total,
            "hit_rate": hit_rate,
            "cache_size": len(self.cache)
        }

# 创建全局缓存实例
template_cache = TemplateCache()

def load_json_file(file_path: str) -> dict:
    logger.info(f"正在加载文件: {file_path}")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"成功加载文件: {file_path}")
        return data
    except Exception as e:
        logger.error(f"加载文件失败 {file_path}: {str(e)}")
        raise

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
    # 首先检查缓存
    cached_result = template_cache.get(text)
    if cached_result is not None:
        logger.debug(f"缓存命中: {text}")
        return cached_result
    
    # 缓存未命中，执行查找
    matching_ids = []
    for id_str, translations in localization_data.items():
        if translations.get('en') == text:
            matching_ids.append(int(id_str))
    
    result = None
    if matching_ids:
        # 如果有多个匹配，返回ID最小的
        result = (str(min(matching_ids)), min(matching_ids))
    
    # 将结果存入缓存（包括未找到的情况）
    template_cache.set(text, result)
    return result if result else (None, None)

def process_station_name(station_name: str, localization_data: Dict) -> str:
    """处理单个空间站名称，返回模板格式"""
    logger.debug(f"\n开始处理空间站名称: {station_name}")
    
    # 处理特殊模式（罗马数字和Moon后的数字）
    # 1. 处理独立的罗马数字（前后有空格的）
    roman_numerals = re.findall(r' ([IVX]+) ', station_name)
    if roman_numerals:
        logger.debug(f"发现罗马数字: {roman_numerals}")
    
    # 2. 处理"Moon"后面的数字
    moon_numbers = re.findall(r'Moon (\d+)', station_name)
    if moon_numbers:
        logger.debug(f"发现Moon数字: {moon_numbers}")
    
    # 处理其他文本部分
    result_parts = []  # 存储最终结果的各个部分
    
    for part in station_name.split(' - '):
        logger.debug(f"\n处理部分: {part}")
        current_part = part.strip()
        processed_part = current_part  # 当前部分的处理结果
        
        # 记录已处理的位置
        processed_positions = set()  # 存储已处理字符的位置
        
        while True:
            # 生成未处理部分的词组组合
            unprocessed_segments = []  # 存储未处理的文本段
            start = 0
            current_segment = ""
            
            # 收集未处理的文本段
            for i, char in enumerate(current_part):
                if i in processed_positions:
                    if current_segment:
                        unprocessed_segments.append(current_segment.strip())
                        current_segment = ""
                else:
                    current_segment += char
            if current_segment:
                unprocessed_segments.append(current_segment.strip())
            
            if not unprocessed_segments:  # 如果没有未处理的部分，退出循环
                break
                
            logger.debug(f"未处理的文本段: {unprocessed_segments}")
            
            found_match = False
            # 对每个未处理的段落尝试匹配
            for segment in unprocessed_segments:
                combinations = generate_word_combinations(segment)
                logger.debug(f"当前处理文本段: {segment}")
                logger.debug(f"生成的词组组合: {combinations}")
                
                for combo in combinations:
                    template_id, _ = find_template_id(combo, localization_data)
                    if template_id:
                        logger.debug(f"找到匹配: {combo} -> {template_id}")
                        # 在原文中定位这个组合
                        start_pos = current_part.find(combo)
                        if start_pos != -1:
                            # 标记这些位置为已处理
                            for i in range(start_pos, start_pos + len(combo)):
                                processed_positions.add(i)
                            # 替换对应位置的文本
                            processed_part = processed_part.replace(combo, f"{{{template_id}}}")
                            found_match = True
                            break
                if found_match:
                    break
            
            if not found_match:
                break
        
        result_parts.append(processed_part)
    
    # 将处理后的部分重新组合
    template = ' - '.join(result_parts)
    
    if template != station_name:
        logger.debug(f"最终处理结果: {template}")
    else:
        logger.warning(f"未能找到任何匹配项: {station_name}")
    
    return template

def main():
    logger.info("开始处理空间站名称模板生成")
    
    try:
        # 加载数据文件
        stations_data = load_json_file('../accounting_entry_types/static_data/stations_202504102216.json')
        localization_data = load_json_file('../accounting_entry_types/output/combined_localization.json')

        # 存储结果的字典
        templates = {}
        
        # 获取总站点数量
        total_stations = len(stations_data['stations'])
        logger.info(f"总计需要处理 {total_stations} 个空间站")
        
        # 处理每个空间站
        for station in tqdm(stations_data['stations'], desc="处理空间站"):
            station_id = station['stationID']
            station_name = station['stationName']
            template = process_station_name(station_name, localization_data)
            templates[station_id] = template
        
        # 获取并记录缓存统计信息
        cache_stats = template_cache.get_stats()
        logger.info("缓存统计信息:")
        logger.info(f"- 缓存命中次数: {cache_stats['hits']}")
        logger.info(f"- 缓存未命中次数: {cache_stats['misses']}")
        logger.info(f"- 缓存命中率: {cache_stats['hit_rate']:.2f}%")
        logger.info(f"- 缓存大小: {cache_stats['cache_size']} 条记录")
        
        # 统计处理结果
        unchanged_count = sum(1 for template in templates.values() if template == stations_data['stations'][0]['stationName'])
        logger.info(f"处理完成: 总计 {total_stations} 个空间站")
        logger.info(f"未变化的模板数量: {unchanged_count}")
        logger.info(f"成功转换的模板数量: {total_stations - unchanged_count}")
        
        # 保存结果
        output_file = 'station_name_templates.json'
        logger.info(f"正在保存结果到: {output_file}")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(templates, f, indent=2, ensure_ascii=False)
        
        # 保存缓存内容
        cache_dict = {}
        for text, result in template_cache.cache.items():
            if result is not None:  # 只保存成功匹配的结果
                template_id, _ = result
                if template_id is not None:
                    cache_dict[text] = template_id
        
        # 按键长度降序排序，这样可以更容易看到长词组在前
        sorted_cache = dict(sorted(cache_dict.items(), key=lambda x: len(x[0]), reverse=True))
        
        cache_file = 'station_name_templates_cache.json'
        logger.info(f"正在保存缓存字典到: {cache_file}")
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(sorted_cache, f, indent=2, ensure_ascii=False)
        
        logger.info("处理完成！")
        
    except Exception as e:
        logger.error(f"处理过程中发生错误: {str(e)}", exc_info=True)
        raise

if __name__ == '__main__':
    main() 