# 从eve本地客户端导出图标，但效果不佳，types.yaml 中缺失了很多图标 iconID
import os
import json
import yaml
import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Set, List, Optional

class LocalIconFetcher:
    def __init__(self):
        # 硬编码的配置
        self.esi_types_url = 'https://esi.evetech.net/latest/universe/types/?datasource=tranquility&page={}'
        self.eve_path = r'E:\EVE'
        self.resfileindex_path = os.path.join(self.eve_path, 'tq', 'resfileindex.txt')
        self.resfiles_path = os.path.join(self.eve_path, 'ResFiles')
        self.iconids_yaml_path = r'..\Data\sde\fsd\iconIDs.yaml'
        self.types_yaml_path = r'..\Data\sde\fsd\types.yaml'
        
        # 缓存文件
        self.typeids_cache = 'typeids_cache.txt'
        self.output_json = 'typeid_to_iconpath.json'
        
        # 统计信息
        self.stats = {
            'total_typeids': 0,
            'found_iconfiles': 0,
            'found_filepaths': 0,
            'missing_iconfiles': [],
            'missing_filepaths': []
        }
    
    def fetch_all_typeids(self) -> List[int]:
        """Fetch all type IDs from ESI API with caching support"""
        # 检查缓存文件是否存在且未过期（1小时内）
        if os.path.exists(self.typeids_cache):
            # 获取文件创建时间
            file_creation_time = os.path.getctime(self.typeids_cache)
            current_time = time.time()
            time_diff = current_time - file_creation_time
            
            # 如果文件创建时间在1小时内（3600秒），使用缓存
            if time_diff < 3600:
                print(f"Reading type IDs from cache file (created {time_diff/60:.1f} minutes ago)...")
                with open(self.typeids_cache, 'r', encoding='utf-8') as f:
                    return [int(line.strip()) for line in f if line.strip().isdigit()]
            else:
                print(f"Cache file is {time_diff/3600:.1f} hours old, refreshing from API...")
        
        print("Fetching type IDs from ESI API...")
        type_ids = set()
        completed_pages = 0
        
        def fetch_page(page):
            try:
                url = self.esi_types_url.format(page)
                response = requests.get(url, timeout=(10, 30))
                
                if response.status_code == 200:
                    return page, response.json()
                elif "Requested page does not exist!" in response.text:
                    return page, None
                else:
                    print(f"\nError fetching page {page}: HTTP {response.status_code}")
                    return page, None
                    
            except Exception as e:
                print(f"\nError occurred while fetching page {page}: {e}")
                return page, None
        
        # First get page 1
        first_page_result = fetch_page(1)
        if first_page_result[1]:
            type_ids.update(first_page_result[1])
            completed_pages = 1
            
            # Use thread pool to fetch remaining pages concurrently
            with ThreadPoolExecutor(max_workers=10) as executor:
                page = 2
                max_concurrent = 20  # Maximum concurrent requests
                futures = {}
                finished = False
                
                while not finished:
                    # Submit new tasks until max concurrent limit
                    while len(futures) < max_concurrent and not finished:
                        future = executor.submit(fetch_page, page)
                        futures[future] = page
                        page += 1
                    
                    # Wait for at least one task to complete
                    if futures:
                        completed_future = next(as_completed(futures))
                        page_num = futures.pop(completed_future)
                        page_num_result, page_data = completed_future.result()
                        
                        if page_data is None:
                            # Page doesn't exist, reached the end
                            finished = True
                        else:
                            type_ids.update(page_data)
                            completed_pages += 1
                            print(f"\rFetched pages: {completed_pages}, Total type IDs: {len(type_ids)}", 
                                  end='', flush=True)
                
                # Wait for all remaining tasks to complete
                for future in futures:
                    page_num_result, page_data = future.result()
                    if page_data is not None:
                        type_ids.update(page_data)
                        completed_pages += 1
                        print(f"\rFetched pages: {completed_pages}, Total type IDs: {len(type_ids)}", 
                              end='', flush=True)
        
        print(f"\nTotal fetched {completed_pages} pages of data, {len(type_ids)} type IDs")
        
        # Save to cache
        type_ids_list = sorted(list(type_ids))
        with open(self.typeids_cache, 'w', encoding='utf-8') as f:
            for type_id in type_ids_list:
                f.write(f"{type_id}\n")
        
        return type_ids_list
    
    def parse_types_yaml(self) -> Dict[int, int]:
        """Parse types.yaml file, return typeid to iconID mapping"""
        print("Parsing types.yaml file...")
        
        if not os.path.exists(self.types_yaml_path):
            raise FileNotFoundError(f"types.yaml file not found: {self.types_yaml_path}")
        
        with open(self.types_yaml_path, 'r', encoding='utf-8') as f:
            types_data = yaml.safe_load(f)
        
        # Convert to typeid to iconID mapping
        typeid_to_iconid = {}
        for typeid_str, data in types_data.items():
            if isinstance(data, dict) and 'iconID' in data:
                typeid = int(typeid_str)
                iconid = int(data['iconID'])
                typeid_to_iconid[typeid] = iconid
        
        print(f"Parsed {len(typeid_to_iconid)} typeid to iconID mappings from types.yaml")
        return typeid_to_iconid
    
    def parse_iconids_yaml(self) -> Dict[int, str]:
        """Parse iconIDs.yaml file, return iconID to iconFile mapping"""
        print("Parsing iconIDs.yaml file...")
        
        if not os.path.exists(self.iconids_yaml_path):
            raise FileNotFoundError(f"iconIDs.yaml file not found: {self.iconids_yaml_path}")
        
        with open(self.iconids_yaml_path, 'r', encoding='utf-8') as f:
            icon_data = yaml.safe_load(f)
        
        # Convert to iconID to iconFile mapping
        iconid_to_iconfile = {}
        for iconid_str, data in icon_data.items():
            if isinstance(data, dict) and 'iconFile' in data:
                iconid = int(iconid_str)
                iconfile = data['iconFile'].lower()  # 转为全小写
                iconid_to_iconfile[iconid] = iconfile
        
        print(f"Parsed {len(iconid_to_iconfile)} iconID to iconFile mappings from iconIDs.yaml")
        return iconid_to_iconfile
    
    def parse_resfileindex(self) -> Dict[str, str]:
        """Parse resfileindex.txt file, return resource path to file path mapping"""
        print("Parsing resfileindex.txt file...")
        
        if not os.path.exists(self.resfileindex_path):
            raise FileNotFoundError(f"resfileindex.txt file not found: {self.resfileindex_path}")
        
        resource_to_filepath = {}
        
        with open(self.resfileindex_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                
                parts = line.split(',')
                if len(parts) >= 2:
                    resource_path = parts[0].lower()  # res:/staticdata/skillplans.fsdbinary
                    file_path = parts[1].lower()      # c7/c7def626ddcfd142_38da240ee9fa6fc94f4993218d5aac53
                    resource_to_filepath[resource_path] = file_path
                else:
                    print(f"Warning: Line {line_num} format incorrect: {line}")
        
        print(f"Parsed {len(resource_to_filepath)} resource mappings from resfileindex.txt")
        return resource_to_filepath
    
    def generate_typeid_to_filepath_mapping(self, type_ids: List[int], 
                                          typeid_to_iconid: Dict[int, int],
                                          iconid_to_iconfile: Dict[int, str],
                                          resource_to_filepath: Dict[str, str]) -> Dict[int, str]:
        """Generate mapping from typeid to local file path"""
        print("Generating typeid to file path mapping...")
        
        typeid_to_filepath = {}
        self.stats['total_typeids'] = len(type_ids)
        
        for typeid in type_ids:
            # Step 1: Find iconID from typeid
            if typeid not in typeid_to_iconid:
                self.stats['missing_iconfiles'].append(typeid)
                continue
            
            iconid = typeid_to_iconid[typeid]
            
            # Step 2: Find iconFile from iconID
            if iconid not in iconid_to_iconfile:
                self.stats['missing_iconfiles'].append(typeid)
                continue
            
            iconfile = iconid_to_iconfile[iconid]
            self.stats['found_iconfiles'] += 1
            
            # Step 3: Find file path from iconFile
            if iconfile not in resource_to_filepath:
                self.stats['missing_filepaths'].append(typeid)
                continue
            
            file_path = resource_to_filepath[iconfile]
            self.stats['found_filepaths'] += 1
            
            # Step 4: Generate complete local file path
            full_path = os.path.join(self.resfiles_path, file_path)
            typeid_to_filepath[typeid] = full_path
        
        return typeid_to_filepath
    
    def save_result(self, typeid_to_filepath: Dict[int, str]):
        """Save result to JSON file"""
        print(f"Saving result to {self.output_json}...")
        
        with open(self.output_json, 'w', encoding='utf-8') as f:
            json.dump(typeid_to_filepath, f, ensure_ascii=False, indent=2)
    
    def print_statistics(self):
        """Print statistics"""
        print("\n" + "="*50)
        print("Processing Statistics:")
        print(f"Total type IDs: {self.stats['total_typeids']}")
        print(f"Found iconFiles: {self.stats['found_iconfiles']}")
        print(f"Found file paths: {self.stats['found_filepaths']}")
        print(f"Missing iconFiles: {len(self.stats['missing_iconfiles'])}")
        print(f"Missing file paths: {len(self.stats['missing_filepaths'])}")
        
        if self.stats['missing_iconfiles']:
            print(f"\nFirst 10 typeids missing iconFile: {self.stats['missing_iconfiles'][:10]}")
            if len(self.stats['missing_iconfiles']) > 10:
                print(f"... and {len(self.stats['missing_iconfiles']) - 10} more")
        
        if self.stats['missing_filepaths']:
            print(f"\nFirst 10 typeids missing file path: {self.stats['missing_filepaths'][:10]}")
            if len(self.stats['missing_filepaths']) > 10:
                print(f"... and {len(self.stats['missing_filepaths']) - 10} more")
        
        print("="*50)
    
    def run(self):
        """Run main process"""
        try:
            # 1. Get all type IDs
            type_ids = self.fetch_all_typeids()
            
            # 2. Parse types.yaml to get typeid -> iconID mapping
            typeid_to_iconid = self.parse_types_yaml()
            
            # 3. Parse iconIDs.yaml to get iconID -> iconFile mapping
            iconid_to_iconfile = self.parse_iconids_yaml()
            
            # 4. Parse resfileindex.txt
            resource_to_filepath = self.parse_resfileindex()
            
            # 5. Generate mapping
            typeid_to_filepath = self.generate_typeid_to_filepath_mapping(
                type_ids, typeid_to_iconid, iconid_to_iconfile, resource_to_filepath
            )
            
            # 6. Save result
            self.save_result(typeid_to_filepath)
            
            # 7. Print statistics
            self.print_statistics()
            
            print(f"\nProcessing completed! Result saved to {self.output_json}")
            
        except Exception as e:
            print(f"Error occurred during processing: {e}")
            raise

def main():
    fetcher = LocalIconFetcher()
    fetcher.run()

if __name__ == '__main__':
    main() 