import os
import json
import shutil
import time
import requests
import subprocess
import sys
import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from PIL import Image

class LocalIconLoader:
    def __init__(self, num_threads=10):
        self.local_icon_dir = 'icon_from_client'
        self.output_dir = 'icon_from_api_and_client'
        self.metadata_file = os.path.join(self.local_icon_dir, 'service_metadata.json')
        self.timeout = (10, 20)  # (连接超时, 读取超时)
        self.max_retries = 5
        self.num_threads = num_threads
        
        # 线程安全锁
        self.not_exist_lock = Lock()
        self.failed_lock = Lock()
        self.bp_lock = Lock()
        
        # 统计计数器
        self.stats = {
            'local_found': 0,
            'local_missing': 0,
            'network_success': 0,
            'network_failed': 0,
            'network_not_exist': 0
        }
        
        # 确保输出目录存在
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 加载本地元数据
        self.local_metadata = self._load_local_metadata()
        print(f"已加载本地元数据，包含 {len(self.local_metadata)} 个type ID")

    def _load_local_metadata(self):
        """加载本地service_metadata.json"""
        if not os.path.exists(self.metadata_file):
            print(f"警告：找不到 {self.metadata_file}")
            return {}
        
        try:
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            # 转换键为整数
            return {int(k): v for k, v in metadata.items()}
        except Exception as e:
            print(f"加载元数据文件时出错: {e}")
            return {}

    def _copy_local_icon(self, type_id, variant='icon'):
        """从本地复制图标文件"""
        if type_id not in self.local_metadata:
            return False
        
        metadata = self.local_metadata[type_id]
        if variant not in metadata:
            return False
        
        filename = metadata[variant]
        source_path = os.path.join(self.local_icon_dir, filename)
        
        if not os.path.exists(source_path):
            return False
        
        # 根据变体确定目标文件名
        if variant == 'icon':
            target_filename = f"{type_id}_64.png"
        elif variant == 'bp':
            target_filename = f"{type_id}_64.png"
        elif variant == 'bpc':
            target_filename = f"{type_id}_bpc_64.png"
        else:
            return False
        
        target_path = os.path.join(self.output_dir, target_filename)
        
        try:
            shutil.copy2(source_path, target_path)
            return True
        except Exception as e:
            print(f"复制文件失败 {source_path} -> {target_path}: {e}")
            return False

    def process_local_icons(self, type_ids):
        """处理本地图标，返回未找到的type_id列表"""
        print("开始处理本地图标...")
        found_locally = set()
        missing_locally = []
        
        for i, type_id in enumerate(type_ids, 1):
            if i % 1000 == 0:
                print(f"处理本地图标进度: {i}/{len(type_ids)} ({i/len(type_ids)*100:.1f}%)")
            
            found = False
            
            # 检查并复制icon变体
            if self._copy_local_icon(type_id, 'icon'):
                found = True
                
            # 检查并复制bp变体
            if self._copy_local_icon(type_id, 'bp'):
                found = True
                
            # 检查并复制bpc变体
            if self._copy_local_icon(type_id, 'bpc'):
                found = True
            
            if found:
                found_locally.add(type_id)
                self.stats['local_found'] += 1
            else:
                missing_locally.append(type_id)
                self.stats['local_missing'] += 1
        
        print(f"\n本地处理完成：")
        print(f"- 本地找到: {len(found_locally)} 个")
        print(f"- 本地缺失: {len(missing_locally)} 个")
        
        return missing_locally

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
                    raise

    def _save_image(self, content, type_id, variant=''):
        """保存图片到文件"""
        if variant == 'bpc':
            filename = f'{type_id}_bpc_64.png'
        else:
            filename = f'{type_id}_64.png'
        
        save_path = os.path.join(self.output_dir, filename)
        with open(save_path, 'wb') as f:
            f.write(content)
        return True

    def _record_bp_id(self, type_id):
        """记录蓝图类型的ID（线程安全）"""
        with self.bp_lock:
            with open('bp_id.txt', 'a') as f:
                f.write(f"{type_id}\n")

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

    def download_icon_from_network(self, type_id):
        """从网络下载指定type ID的图标（复用sync_icon.py的逻辑）"""
        try:
            # 1. 首先尝试常见的变体
            common_variants = ['icon', 'bp']
            for variant in common_variants:
                url = f'https://images.evetech.net/types/{type_id}/{variant}?size=64'
                try:
                    response = self._make_request(url, f"获取{type_id} 的 {variant} 时网络错误")
                    if response.status_code == 200 and b"bad category or variation" not in response.content:
                        # 如果成功获取到bp图标，尝试获取bpc图标并记录type_id
                        if variant == 'bp':
                            self._record_bp_id(type_id)
                            bpc_url = f'https://images.evetech.net/types/{type_id}/bpc?size=64'
                            try:
                                bpc_response = self._make_request(bpc_url, f"获取{type_id} 的 bpc 时网络错误")
                                if bpc_response.status_code == 200 and b"bad category or variation" not in bpc_response.content:
                                    self._save_image(bpc_response.content, type_id, 'bpc')
                            except (requests.exceptions.RequestException, IOError):
                                pass
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
                    pass
                    
            # 所有尝试都失败，记录为不存在
            self._record_not_exist(type_id)
            return 'not_exist'
            
        except (requests.exceptions.RequestException, IOError):
            # 所有重试都失败，记录到failed.txt
            self._record_failed(type_id)
            return 'failed'

    def download_missing_icons(self, missing_type_ids):
        """并发下载缺失的图标"""
        if not missing_type_ids:
            print("没有需要从网络下载的图标")
            return
        
        print(f"\n开始从网络下载 {len(missing_type_ids)} 个缺失的图标:")
        for item in missing_type_ids:
            print(item)
        print()
        completed = 0
        
        def download_with_progress(type_id):
            nonlocal completed
            result = self.download_icon_from_network(type_id)
            completed += 1
            print(f"\r网络下载进度: {completed}/{len(missing_type_ids)} ({completed/len(missing_type_ids)*100:.1f}%) - 处理 Type ID {type_id} - {result}", 
                  end='', flush=True)
            return result

        with ThreadPoolExecutor(max_workers=self.num_threads) as executor:
            future_to_id = {executor.submit(download_with_progress, tid): tid 
                          for tid in missing_type_ids}
            
            for future in as_completed(future_to_id):
                try:
                    result = future.result()
                    if result is True:
                        self.stats['network_success'] += 1
                    elif result == 'not_exist':
                        self.stats['network_not_exist'] += 1
                    elif result == 'failed':
                        self.stats['network_failed'] += 1
                except Exception as e:
                    type_id = future_to_id[future]
                    print(f"\n处理 Type ID {type_id} 时发生错误: {e}")
                    self.stats['network_failed'] += 1

def read_types_from_api(force_reload=False):
    """从ESI API获取所有type IDs（复用sync_icon.py的逻辑）"""
    # 读取not_exist.txt中的ID
    not_exist_ids = set()
    if os.path.exists('not_exist.txt'):
        with open('not_exist.txt', 'r') as f:
            not_exist_ids = {int(line.strip()) for line in f if line.strip().isdigit()}
    
    # 首先检查是否存在缓存的typeids.txt
    if os.path.exists('typeids.txt') and not force_reload:
        print("从缓存文件读取type IDs...")
        with open('typeids.txt', 'r') as f:
            type_ids = [int(line.strip()) for line in f.readlines()]
            return [tid for tid in type_ids if tid not in not_exist_ids]
    
    print("从ESI API获取type IDs...")
    type_ids = set()
    completed_pages = 0
    
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
    
    # 先获取第一页
    first_page_result = fetch_page(1)
    if first_page_result[1]:
        type_ids.update(first_page_result[1])
        completed_pages = 1
        
        # 使用线程池并发获取剩余页面
        with ThreadPoolExecutor(max_workers=10) as executor:
            page = 2
            futures = []
            total_pages = None
            
            while True:
                future = executor.submit(fetch_page, page)
                futures.append(future)
                page += 1
                
                for future in [f for f in futures if f.done()]:
                    futures.remove(future)
                    page_num, page_data = future.result()
                    
                    if page_data is None:
                        total_pages = page_num - 1
                        break
                    
                    type_ids.update(page_data)
                    completed_pages += 1
                    print(f"\r已获取页面: {completed_pages}, 累计获取: {len(type_ids)} 个type IDs", 
                          end='', flush=True)
                
                if total_pages is not None:
                    break
                
                time.sleep(0.1)
            
            # 等待所有进行中的任务完成
            for future in futures:
                page_num, page_data = future.result()
                if page_data is not None:
                    type_ids.update(page_data)
                    completed_pages += 1
                    print(f"\r已获取页面: {completed_pages}, 累计获取: {len(type_ids)} 个type IDs", 
                          end='', flush=True)
    
    print(f"\n总共获取了 {completed_pages} 页数据")
    print("保存type IDs到缓存文件...")
    type_ids = sorted(list(type_ids))
    with open('typeids.txt', 'w') as f:
        for type_id in type_ids:
            f.write(f"{type_id}\n")
    
    return [tid for tid in type_ids if tid not in not_exist_ids]

def main(num_threads=30):
    """主函数"""
    print("开始混合图标加载流程...")
    print("=" * 50)
    
    # 0. 询问是否重新加载type_id
    force_reload = False
    if os.path.exists('typeids.txt'):
        choice = input("发现缓存的type ID列表，是否重新从网络获取最新的type ID列表？(y/n): ").lower().strip()
        if choice == 'y':
            force_reload = True
            print("将重新从网络获取type ID列表...")
        else:
            print("使用缓存的type ID列表...")
    
    # 1. 获取所有type IDs
    print("\n步骤1: 获取所有type IDs")
    type_ids = read_types_from_api(force_reload)
    print(f"总共发现 {len(type_ids)} 个type ID")
    
    # 2. 创建加载器并处理本地图标
    print("\n步骤2: 处理本地图标")
    loader = LocalIconLoader(num_threads=num_threads)
    missing_type_ids = loader.process_local_icons(type_ids)
    
    # 3. 下载缺失的图标
    print("\n步骤3: 下载缺失的图标")
    loader.download_missing_icons(missing_type_ids)
    
    # 4. 输出统计信息
    print("\n" + "=" * 50)
    print("处理完成！统计信息：")
    print(f"本地找到: {loader.stats['local_found']}")
    print(f"本地缺失: {loader.stats['local_missing']}")
    print(f"网络下载成功: {loader.stats['network_success']}")
    print(f"网络资源不存在: {loader.stats['network_not_exist']}")
    print(f"网络下载失败: {loader.stats['network_failed']}")
    
    total_success = loader.stats['local_found'] + loader.stats['network_success']
    print(f"\n总成功: {total_success}/{len(type_ids)} ({total_success/len(type_ids)*100:.2f}%)")
    
    print(f"\n所有图标已保存到: {loader.output_dir}")
    
    # 5. 检查和压缩图标尺寸
    print("\n步骤5: 检查和压缩图标尺寸")
    resize_oversized_icons(loader.output_dir)
    
    # 6. 执行后续的replace_icon.py流程
    print("\n步骤6: 执行图标替换流程")
    run_replace_icon_script(loader.output_dir)
    
    # 7. 记录完成时间戳
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("./last_fetch.txt", "w") as f:
        f.write(timestamp)
    print(f"\n已记录完成时间: {timestamp}")
    
    print("\n所有操作已完成！")

def resize_oversized_icons(icon_dir):
    """检查并压缩大于64x64的图标"""
    if not os.path.exists(icon_dir):
        print(f"图标目录 {icon_dir} 不存在，跳过尺寸检查")
        return
    
    target_size = (64, 64)
    processed_count = 0
    error_count = 0
    total_files = 0
    
    print(f"开始检查目录 {icon_dir} 中的图标尺寸...")
    
    # 获取所有PNG文件
    png_files = [f for f in os.listdir(icon_dir) if f.lower().endswith('.png')]
    total_files = len(png_files)
    
    if total_files == 0:
        print("未找到PNG文件")
        return
    
    for i, filename in enumerate(png_files, 1):
        file_path = os.path.join(icon_dir, filename)
        
        try:
            with Image.open(file_path) as img:
                original_size = img.size
                
                # 检查是否需要压缩
                if original_size[0] > target_size[0] or original_size[1] > target_size[1]:
                    # 使用高质量的重采样算法压缩图片
                    resized_img = img.resize(target_size, Image.Resampling.LANCZOS)
                    
                    # 保存压缩后的图片
                    resized_img.save(file_path, 'PNG', optimize=True)
                    processed_count += 1
                    
                    if i % 100 == 0 or processed_count <= 10:
                        print(f"压缩 {filename}: {original_size} -> {target_size}")
                
                # 显示进度
                if i % 1000 == 0:
                    print(f"进度: {i}/{total_files} ({i/total_files*100:.1f}%)")
                    
        except Exception as e:
            error_count += 1
            print(f"处理文件 {filename} 时出错: {e}")
    
    print(f"\n图标尺寸检查完成:")
    print(f"总文件数: {total_files}")
    print(f"压缩文件数: {processed_count}")
    print(f"错误文件数: {error_count}")

def run_replace_icon_script(source_dir):
    """运行replace_icon.py脚本，传递源目录参数"""
    try:
        print(f"开始执行 replace_icon.py，源目录: {source_dir}")
        # 导入并调用replace_icon的函数，传递源目录参数
        from replace_icon import copy_icons_from_source, copy_icon_batch
        copy_icons_from_source(source_dir)
        
        # 只有从icon_from_api复制时才需要执行copy_icon_batch进行图标修复
        # 因为本地客户端的图标已经是正确的，不需要修复
        if "icon_from_api_and_client" not in source_dir:
            print("执行图标修复流程...")
            copy_icon_batch()
        else:
            print("使用本地客户端图标，跳过图标修复流程")
            
        print("replace_icon.py 执行完成")
    except Exception as e:
        print(f"执行 replace_icon.py 时出错: {e}")

if __name__ == '__main__':
    main(num_threads=30) 