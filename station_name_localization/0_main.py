import os
import subprocess
import sys
import shutil

def run_script(script_name):
    """运行指定的Python脚本"""
    try:
        print(f"\n开始执行 {script_name}...")
        subprocess.run([sys.executable, script_name], check=True)
        print(f"{script_name} 执行完成")
    except subprocess.CalledProcessError as e:
        print(f"执行 {script_name} 时出错: {e}")
        sys.exit(1)


def delete_files():
    """删除指定的文件和目录"""
    files_to_delete = [
        'station_name_templates.json',
        'station_name_templates_cache.json'
    ]
    print("\n开始重新构建数据资源...")
    # 删除文件
    for file in files_to_delete:
        if os.path.exists(file):
            try:
                os.remove(file)
                print(f"已删除文件: {file}")
            except Exception as e:
                print(f"删除文件 {file} 时出错: {e}")

if __name__ == "__main__":
    choice = input("是否重新构建资源？(y/n)(y:重新计算文本模板,n:复用现有模板): ").lower().strip()

    if choice == 'y':
        delete_files()
    else:
        print("\n跳过重新构建，直接执行同步...")

    run_script("1_station_template_generator.py")