#!/usr/bin/env python3
"""
依赖安装脚本
自动安装所需的Python包
"""

import subprocess
import sys

def install_package(package):
    """安装Python包"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✓ 成功安装 {package}")
        return True
    except subprocess.CalledProcessError:
        print(f"✗ 安装 {package} 失败")
        return False

def main():
    print("=== 台风可视化程序依赖安装 ===")
    
    # 基础依赖
    basic_packages = [
        "pandas>=2.0.0",
        "numpy>=1.20.0"
    ]
    
    # 简化版本依赖
    simple_packages = [
        "matplotlib>=3.5.0",
        "cartopy>=0.21.0"
    ]
    
    # 动画版本依赖
    pygame_packages = [
        "pygame>=2.0.0"
    ]
    
    print("选择要安装的版本:")
    print("1. 只安装基础依赖")
    print("2. 安装简化版本依赖 (推荐)")
    print("3. 安装动画版本依赖")
    print("4. 安装所有依赖")
    
    choice = input("请输入选择 (1-4, 默认2): ").strip() or "2"
    
    packages_to_install = []
    
    if choice in ["1", "2", "3", "4"]:
        packages_to_install.extend(basic_packages)
    
    if choice in ["2", "4"]:
        packages_to_install.extend(simple_packages)
    
    if choice in ["3", "4"]:
        packages_to_install.extend(pygame_packages)
    
    if not packages_to_install:
        print("无效选择")
        return
    
    print(f"\n将安装以下包: {', '.join(packages_to_install)}")
    confirm = input("确认安装? (y/N): ").strip().lower()
    
    if confirm != 'y':
        print("取消安装")
        return
    
    print("\n开始安装...")
    success_count = 0
    
    for package in packages_to_install:
        if install_package(package):
            success_count += 1
    
    print(f"\n安装完成: {success_count}/{len(packages_to_install)} 个包安装成功")
    
    if success_count == len(packages_to_install):
        print("✓ 所有依赖安装成功！现在可以运行程序了。")
        print("\n运行方式:")
        if choice in ["2", "4"]:
            print("  python3 simple_typhoon_viz.py  # 简化版本")
        if choice in ["3", "4"]:
            print("  python3 main.py  # 动画版本")
        print("  python3 run_demo.py  # 演示脚本")
    else:
        print("⚠ 部分依赖安装失败，请手动安装失败的包")

if __name__ == '__main__':
    main()
