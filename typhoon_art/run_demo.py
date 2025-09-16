#!/usr/bin/env python3
"""
台风可视化演示脚本
提供两个版本的选择：
1. 简化的matplotlib版本 (推荐)
2. 原始的pygame动画版本
"""

import sys
import os

def main():
    print("=== 台风轨迹可视化演示 ===")
    print("请选择要运行的版本:")
    print("1. 简化版本 (matplotlib) - 推荐，更清晰易懂")
    print("2. 动画版本 (pygame) - 动态螺旋效果")
    print("3. 退出")
    
    while True:
        choice = input("\n请输入选择 (1-3): ").strip()
        
        if choice == '1':
            print("\n启动简化版本...")
            try:
                from simple_typhoon_viz import main as simple_main
                simple_main()
            except ImportError as e:
                print(f"错误: 无法导入简化版本 - {e}")
                print("请确保安装了必要的依赖: pip install matplotlib cartopy")
            except Exception as e:
                print(f"运行时错误: {e}")
            break
            
        elif choice == '2':
            print("\n启动动画版本...")
            try:
                from main import main as pygame_main
                pygame_main(sys.argv)
            except ImportError as e:
                print(f"错误: 无法导入动画版本 - {e}")
                print("请确保安装了必要的依赖: pip install pygame pandas numpy")
            except Exception as e:
                print(f"运行时错误: {e}")
            break
            
        elif choice == '3':
            print("退出程序")
            break
            
        else:
            print("无效选择，请输入 1、2 或 3")

if __name__ == '__main__':
    main()
