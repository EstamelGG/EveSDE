import os
import requests
import yaml
import time
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from typing import Dict, List, Any
from pathlib import Path

class TypeDetailFetcher:
    def __init__(self, num_threads=50):
        self.save_dir = Path("type_details")
        self.timeout = (5, 10)  # (连接超时, 读取超时)
        self.max_retries = 5
        self.num_threads = num_threads
        self.failed_lock = Lock()
        self.save_dir.mkdir(exist_ok=True)
        
    def _make_request(self, url, retry_message="网络错误"):
        """统一的请求处理函数，包含重试逻辑"""
        retry_count = 0
        while retry_count < self.max_retries:
            try:
                response = requests.get(url, timeout=self.timeout)
                return response
            except (requests.exceptions.RequestException, IOError) as e:
                retry_count += 1
                if retry_count < self.max_retries:
                    print(f"\n{retry_message} {e}，等待1秒后进行第{retry_count + 1}/{self.max_retries}次重试...")
                    time.sleep(1)
                else:
                    raise  # 重试耗尽，抛出异常

    def _record_failed(self, type_id):
        """记录下载失败的ID（线程安全）"""
        with self.failed_lock:
            with open('failed.txt', 'a') as f:
                f.write(f"{type_id}\n")

    def fetch_type_detail(self, type_id, skip_existing=True):
        """获取单个type_id的详细信息"""
        # 检查是否已存在
        file_path = self.save_dir / f"{type_id}.json"
        if file_path.exists() and skip_existing:
            return 'exists'
            
        try:
            url = f"https://esi.evetech.net/latest/universe/types/{type_id}/?datasource=tranquility&language=en"
            response = self._make_request(url, f"获取type_id {type_id} 时网络错误")
            if response.status_code == 200:
                details = response.json()
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(details, f, ensure_ascii=False, indent=2)
                return 'success'
            else:
                return 'failed'
        except Exception as e:
            print(f"\n处理type_id {type_id} 时发生错误: {e}")
            self._record_failed(type_id)
            return 'failed'

    def fetch_batch(self, type_ids, skip_existing=True):
        """并发获取一批type的详细信息"""
        results = {'success': 0, 'failed': 0, 'skip': 0}
        total = len(type_ids)
        completed = 0

        def fetch_with_progress(type_id):
            nonlocal completed
            result = self.fetch_type_detail(type_id, skip_existing)
            completed += 1
            print(f"\r进度: {completed}/{total} ({completed/total*100:.1f}%) - 处理 Type ID {type_id} - {result}", 
                  end='', flush=True)
            return result

        with ThreadPoolExecutor(max_workers=self.num_threads) as executor:
            future_to_id = {executor.submit(fetch_with_progress, tid): tid 
                          for tid in type_ids}
            
            for future in as_completed(future_to_id):
                try:
                    result = future.result()
                    if result == 'exists':
                        results['skip'] += 1
                    elif result == 'success':
                        results['success'] += 1
                    elif result == 'failed':
                        results['failed'] += 1
                except Exception as e:
                    type_id = future_to_id[future]
                    print(f"\n处理 Type ID {type_id} 时发生错误: {e}")
                    results['failed'] += 1

        return results

def read_types_yaml():
    """读取或获取所有type ID"""
    # 首先检查是否存在缓存的typeids.txt
    if os.path.exists('typeids.txt'):
        print("从缓存文件读取type IDs...")
        with open('typeids.txt', 'r') as f:
            type_ids = [int(line.strip()) for line in f.readlines()]
            return type_ids
    
    print("从ESI API获取type IDs...")
    type_ids = set()
    completed_pages = 0
    total_pages = None
    
    def fetch_page(page):
        try:
            url = f'https://esi.evetech.net/latest/universe/types/?datasource=tranquility&page={page}'
            response = requests.get(url, timeout=(5, 10))
            
            if response.status_code == 200:
                return page, response.json()
            elif "Requested page does not exist!" in response.text:
                return page, None
            else:
                print(f"\n获取第 {page} 页时出错: HTTP {response.status_code}")
                return page, None
                
        except Exception as e:
            print(f"\n获取第 {page} 页时发生错误: {e}")
            return page, None
    
    # 先获取第一页来确定总页数
    first_page_result = fetch_page(1)
    if first_page_result[1]:
        type_ids.update(first_page_result[1])
        completed_pages = 1
        
        # 使用线程池并发获取剩余页面
        with ThreadPoolExecutor(max_workers=10) as executor:
            page = 2
            futures = []
            
            while True:
                # 提交新的任务
                future = executor.submit(fetch_page, page)
                futures.append(future)
                page += 1
                
                # 处理完成的任务
                for future in [f for f in futures if f.done()]:
                    futures.remove(future)
                    page_num, page_data = future.result()
                    
                    if page_data is None:
                        # 如果页面不存在，说明已经到达末尾
                        total_pages = page_num - 1
                        break
                    
                    type_ids.update(page_data)
                    completed_pages += 1
                    print(f"\r已获取页面: {completed_pages}, 累计获取: {len(type_ids)} 个type IDs", 
                          end='', flush=True)
                
                if total_pages is not None:
                    break
                
                time.sleep(0.1)  # 小延迟避免过快提交任务
            
            # 等待所有进行中的任务完成
            for future in futures:
                page_num, page_data = future.result()
                if page_data is not None:
                    type_ids.update(page_data)
                    completed_pages += 1
                    print(f"\r已获取页面: {completed_pages}, 累计获取: {len(type_ids)} 个type IDs", 
                          end='', flush=True)
    
    print(f"\n总共获取了 {completed_pages} 页数据")
    print("\n保存type IDs到缓存文件...")
    type_ids = sorted(list(type_ids))  # 转换为排序列表
    with open('typeids.txt', 'w') as f:
        for type_id in type_ids:
            f.write(f"{type_id}\n")
    
    return type_ids

def format_dogma_data(type_details: Dict[str, Any]) -> Dict[str, Any]:
    """格式化dogma数据为指定格式"""
    dogma_data = {}
    
    # 处理attributes
    attributes = []
    for attr in type_details.get("dogma_attributes", []):
        # 跳过attribute_id=4的数据
        if attr["attribute_id"] == 4:
            continue
        attributes.append({
            "attributeID": attr["attribute_id"],
            "value": float(attr["value"])  # 转换为float以避免科学计数法
        })
    
    # 处理effects
    effects = []
    for effect in type_details.get("dogma_effects", []):
        effects.append({
            "effectID": effect["effect_id"],
            "isDefault": effect["is_default"]
        })
    
    # 按ID排序
    attributes.sort(key=lambda x: x["attributeID"])
    effects.sort(key=lambda x: x["effectID"])
    
    # 只有当attributes或effects不为空时才添加到结果中
    if attributes:
        dogma_data["dogmaAttributes"] = attributes
    if effects:
        dogma_data["dogmaEffects"] = effects
    
    return dogma_data

def generate_yaml():
    """从所有json文件生成最终的yaml文件"""
    type_dir = Path("type_details")
    result = {}
    
    print("\n开始生成YAML文件...")
    total_files = len(list(type_dir.glob("*.json")))
    processed = 0
    
    for file in type_dir.glob("*.json"):
        type_id = int(file.stem)
        with open(file, "r", encoding="utf-8") as f:
            details = json.load(f)
            dogma_data = format_dogma_data(details)
            # 只有当dogma_data不为空时才添加到结果中
            if dogma_data:
                result[type_id] = dogma_data
        processed += 1
        print(f"\r处理进度: {processed}/{total_files} ({processed/total_files*100:.1f}%)", 
              end='', flush=True)
    
    print("\n保存YAML文件...")
    with open("typeDogma.yaml", "w", encoding="utf-8") as f:
        yaml.dump(result, f, allow_unicode=True, default_flow_style=False)
    print("YAML文件生成完成！")

def main():
    print("欢迎使用Type信息获取工具")
    
    # 询问是否重新构建
    choice = input("是否重新构建所有type信息？(y/n): ").lower().strip()
    if choice == 'y':
        type_dir = Path("type_details")
        if type_dir.exists():
            for file in type_dir.glob("*.json"):
                file.unlink()
            print("已删除所有type json文件")
    
    # 获取所有type_id
    type_ids = read_types_yaml()
    print(f"总共发现 {len(type_ids)} 个type ID")
    print(f"跳过已存在文件: {'是' if choice != 'y' else '否'}")
    
    # 使用多线程获取type详情
    fetcher = TypeDetailFetcher(num_threads=50)
    results = fetcher.fetch_batch(type_ids, skip_existing=(choice != 'y'))
    
    print(f"\n\n获取完成！")
    print(f"成功: {results['success']}")
    print(f"失败: {results['failed']}")
    print(f"已存在跳过: {results['skip']}")
    
    # 生成最终的yaml文件
    generate_yaml()

if __name__ == "__main__":
    main() 