import os
import time
import requests
from ruamel.yaml import YAML

class IconDownloader:
    def __init__(self):
        self.save_dir = './icon_from_api'
        self.timeout = (5, 10)  # (连接超时, 读取超时)
        self.max_retries = 5
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
                    response = self._make_request(url, f"获取{variant}时网络错误")
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
        """记录不存在的ID"""
        with open('not_exist.txt', 'a') as f:
            f.write(f"{type_id}\n")
            
    def _record_failed(self, type_id):
        """记录下载失败的ID"""
        with open('failed.txt', 'a') as f:
            f.write(f"{type_id}\n")

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

def main(skip_existing=True):
    type_ids = read_types_yaml()
    print(f"总共发现 {len(type_ids)} 个type ID")
    print(f"跳过已存在文件: {'是' if skip_existing else '否'}")
    
    downloader = IconDownloader()
    success_count = not_exist_count = failed_count = skip_count = 0
    
    for i, type_id in enumerate(type_ids, 1):
        print(f"正在处理 {i}/{len(type_ids)}: Type ID {type_id}", end='')
        
        result = downloader.download_icon(type_id, skip_existing)
        if result == 'exists':
            skip_count += 1
            print(" - 已存在，跳过")
        elif result is True:
            success_count += 1
            print(" - 成功")
        elif result == 'not_exist':
            not_exist_count += 1
            print(" - 资源不存在")
        elif result == 'failed':
            failed_count += 1
            print(" - 网络错误")
    
    print(f"\n下载完成！")
    print(f"成功: {success_count}")
    print(f"资源不存在: {not_exist_count}")
    print(f"网络错误: {failed_count}")
    print(f"已存在跳过: {skip_count}")

if __name__ == '__main__':
    main(skip_existing=True)
