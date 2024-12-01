import json
import re
import logging
from typing import Dict, List, Tuple, Optional
from tqdm import tqdm
from datetime import datetime
import os

# 配置日志
logging.basicConfig(
    level=logging.ERROR,  # 改为ERROR级别以显示更少信息
    format='%(asctime)s - %(levelname)s - %(message)s'
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
    
    def load_from_file(self, file_path: str) -> bool:
        """从文件加载缓存"""
        try:
            if os.path.exists(file_path):
                logger.info(f"正在从文件加载缓存: {file_path}")
                with open(file_path, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    # 将加载的数据转换为正确的格式
                    for text, template_id in cache_data.items():
                        # 将字符串ID转换为元组格式 (str_id, int_id)
                        self.cache[text] = (template_id, int(template_id))
                logger.info(f"成功加载缓存，包含 {len(cache_data)} 条记录")
                return True
            return False
        except Exception as e:
            logger.error(f"加载缓存文件失败: {str(e)}")
            return False

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
    
    # 将空间站名称按 " - " 分割
    parts = station_name.split(" - ")
    result_parts = []
    
    for part in parts:
        logger.debug(f"\n处理部分: {part}")
        words = part.split()
        processed_words = []
        
        i = 0
        while i < len(words):
            word = words[i]
            
            # 跳过单独的数字
            if word.isdigit():
                processed_words.append(word)
                i += 1
                continue
                
            # 跳过罗马数字
            if re.match(r'^[IVX]+$', word):
                processed_words.append(word)
                i += 1
                continue
            
            # 尝试匹配最长的词组
            max_length = len(words) - i
            found_match = False
            
            for length in range(max_length, 0, -1):
                combo = ' '.join(words[i:i+length])
                template_id, _ = find_template_id(combo, localization_data)
                
                if template_id:
                    processed_words.append(f"{{{template_id}}}")
                    i += length
                    found_match = True
                    logger.debug(f"找到匹配: {combo} -> {template_id}")
                    break
            
            if not found_match:
                processed_words.append(word)
                i += 1
        
        # 将处理后的词组重新组合
        result_parts.append(' '.join(processed_words))
    
    # 将所有部分用 " - " 连接
    template = ' - '.join(result_parts)
    
    if template != station_name:
        logger.debug(f"最终处理结果: {template}")
    else:
        logger.warning(f"未能找到任何匹配项: {station_name}")
    
    return template

def main():
    logger.info("开始处理空间站名称模板生成")
    
    try:
        # 尝试加载缓存文件
        cache_file = 'station_name_templates_cache.json'
        template_cache.load_from_file(cache_file)
        
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
        
        logger.info(f"正在保存缓存字典到: {cache_file}")
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(sorted_cache, f, indent=2, ensure_ascii=False)
        
        logger.info("处理完成！")
        
    except Exception as e:
        logger.error(f"处理过程中发生错误: {str(e)}", exc_info=True)
        raise

if __name__ == '__main__':
    main() 