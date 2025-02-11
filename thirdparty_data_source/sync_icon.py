import os
import time
import requests
from ruamel.yaml import YAML
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

class IconDownloader:
    def __init__(self, num_threads=10):
        self.save_dir = './icon_from_api'
        self.timeout = (5, 10)  # (连接超时, 读取超时)
        self.max_retries = 5
        self.num_threads = num_threads
        # 添加锁用于线程安全的文件写入
        self.not_exist_lock = Lock()
        self.failed_lock = Lock()
        os.makedirs(self.save_dir, exist_ok=True)
        
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
                    print(f"\n{retry_message} {e}，等待1秒后进行第{retry_count + 1}次重试...")
                    time.sleep(1)
                else:
                    raise  # 重试耗尽，抛出异常
        
    def _save_image(self, content, type_id):
        """保存图片到文件"""
        save_path = os.path.join(self.save_dir, f'{type_id}_64.png')
        with open(save_path, 'wb') as f:
            f.write(content)
        return True

    def download_icon(self, type_id, skip_existing=True):
        """下载指定type ID的图标"""
        # 检查是否已存在
        save_path = os.path.join(self.save_dir, f'{type_id}_64.png')
        if os.path.exists(save_path) and skip_existing:
            return 'exists'
            
        try:
            # 1. 首先尝试常见的变体
            common_variants = ['icon', 'bp']
            for variant in common_variants:
                url = f'https://images.evetech.net/types/{type_id}/{variant}?size=64'
                try:
                    response = self._make_request(url, f"获取{type_id} 的 {variant}时网络错误")
                    if response.status_code == 200 and b"bad category or variation" not in response.content:
                        return self._save_image(response.content, type_id)
                except (requests.exceptions.RequestException, IOError):
                    continue
                
            # 2. 如果常见变体都失败，获取可用的变体列表
            variants_url = f'https://images.evetech.net/types/{type_id}/'
            response = self._make_request(variants_url, "获取变体列表时网络错误")
            
            # 如果返回404，说明ID不存在
            if response.status_code == 404:
                self._record_not_exist(type_id)
                return 'not_exist'
                
            if response.status_code == 200:
                try:
                    variants = response.json()
                    # 3. 尝试列表中的其他变体（排除已尝试过的）
                    other_variants = [v for v in variants if v not in common_variants]
                    for variant in other_variants:
                        variant_url = f'https://images.evetech.net/types/{type_id}/{variant}?size=64'
                        try:
                            response = self._make_request(variant_url, f"获取{variant}变体时网络错误")
                            if response.status_code == 200 and b"bad category or variation" not in response.content:
                                return self._save_image(response.content, type_id)
                        except (requests.exceptions.RequestException, IOError):
                            continue
                except (ValueError, IndexError):
                    pass  # JSON解析错误或空列表
                    
            # 所有尝试都失败，记录为不存在
            self._record_not_exist(type_id)
            return 'not_exist'
            
        except (requests.exceptions.RequestException, IOError):
            # 所有重试都失败，记录到failed.txt
            self._record_failed(type_id)
            return 'failed'

    def _record_not_exist(self, type_id):
        """记录不存在的ID（线程安全）"""
        with self.not_exist_lock:
            with open('not_exist.txt', 'a') as f:
                f.write(f"{type_id}\n")
            
    def _record_failed(self, type_id):
        """记录下载失败的ID（线程安全）"""
        with self.failed_lock:
            with open('failed.txt', 'a') as f:
                f.write(f"{type_id}\n")

    def download_batch(self, type_ids, skip_existing=True):
        """并发下载一批图标"""
        results = {'success': 0, 'not_exist': 0, 'failed': 0, 'skip': 0}
        total = len(type_ids)
        completed = 0

        def download_with_progress(type_id):
            nonlocal completed
            result = self.download_icon(type_id, skip_existing)
            completed += 1
            print(f"\r进度: {completed}/{total} ({completed/total*100:.1f}%) - 处理 Type ID {type_id} - {result}", 
                  end='', flush=True)
            return result

        with ThreadPoolExecutor(max_workers=self.num_threads) as executor:
            future_to_id = {executor.submit(download_with_progress, tid): tid 
                          for tid in type_ids}
            
            for future in as_completed(future_to_id):
                try:
                    result = future.result()
                    if result == 'exists':
                        results['skip'] += 1
                    elif result is True:
                        results['success'] += 1
                    elif result == 'not_exist':
                        results['not_exist'] += 1
                    elif result == 'failed':
                        results['failed'] += 1
                except Exception as e:
                    type_id = future_to_id[future]
                    print(f"\n处理 Type ID {type_id} 时发生错误: {e}")
                    results['failed'] += 1

        return results

def read_types_yaml():
    """读取types.yaml文件并返回所有type ID"""
    EXCLUDED_GROUP_IDS = {1950, 1951, 1952, 1953, 1954, 1955, 4040}
    
    # 读取not_exist.txt中的ID
    not_exist_ids = set()
    if os.path.exists('not_exist.txt'):
        with open('not_exist.txt', 'r') as f:
            not_exist_ids = {int(line.strip()) for line in f if line.strip().isdigit()}
    
    # 首先检查是否存在缓存的typeids.txt
    if os.path.exists('typeids.txt'):
        print("从缓存文件读取type IDs...")
        with open('typeids.txt', 'r') as f:
            type_ids = [int(line.strip()) for line in f.readlines()]
            return [tid for tid in type_ids if tid not in not_exist_ids]
    
    print("从types.yaml读取type IDs...")
    yaml = YAML(typ='safe')
    with open('../Data/sde/fsd/types.yaml', 'r', encoding='utf-8') as file:
        types_data = yaml.load(file)
    
    type_ids = []
    for type_id, type_info in types_data.items():
        if isinstance(type_info, dict) and 'groupID' in type_info:
            if type_info['groupID'] not in EXCLUDED_GROUP_IDS and type_id not in not_exist_ids:
                type_ids.append(type_id)
    
    print("保存type IDs到缓存文件...")
    with open('typeids.txt', 'w') as f:
        for type_id in type_ids:
            f.write(f"{type_id}\n")
    
    return type_ids

def main(skip_existing=True, num_threads=10):
    type_ids = read_types_yaml()
    print(f"总共发现 {len(type_ids)} 个type ID")
    print(f"跳过已存在文件: {'是' if skip_existing else '否'}")
    print(f"使用线程数: {num_threads}")
    
    downloader = IconDownloader(num_threads=num_threads)
    results = downloader.download_batch(type_ids, skip_existing)
    
    print(f"\n\n下载完成！")
    print(f"成功: {results['success']}")
    print(f"资源不存在: {results['not_exist']}")
    print(f"网络错误: {results['failed']}")
    print(f"已存在跳过: {results['skip']}")

if __name__ == '__main__':
    main(skip_existing=False, num_threads=50)
