"""
简化的台风轨迹可视化程序
参考用户提供的matplotlib代码，使用更简单清晰的方式显示台风轨迹
"""
import pandas as pd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np
from datetime import datetime
import os

def load_typhoon_data(csv_path):
    """加载台风数据并清洗"""
    print(f"正在加载数据: {csv_path}")
    
    # 读取CSV文件
    df = pd.read_csv(csv_path, low_memory=False)
    print(f"原始数据行数: {len(df)}")
    print(f"列名: {list(df.columns[:10])}...")
    
    # 选择需要的列并重命名
    storms = df[['SID', 'NAME', 'SEASON', 'ISO_TIME', 'LAT', 'LON', 'WMO_WIND']].copy()
    
    # 清洗数据
    storms = storms.dropna(subset=['LAT', 'LON'])  # 移除缺失经纬度的数据
    storms = storms[storms['SEASON'] >= 2000]  # 只选择2000年后的数据
    
    # 处理风速数据
    storms['WMO_WIND'] = pd.to_numeric(storms['WMO_WIND'], errors='coerce').fillna(0)
    
    print(f"清洗后数据行数: {len(storms)}")
    print(f"台风数量: {storms['SID'].nunique()}")
    
    return storms

def plot_typhoon_tracks(storms, num_tracks=5):
    """绘制台风轨迹"""
    # 获取一些示例台风
    unique_storms = storms['SID'].unique()
    selected_storms = unique_storms[:num_tracks]
    
    # 创建图形
    plt.figure(figsize=(12, 8))
    ax = plt.axes(projection=ccrs.PlateCarree())
    
    # 设置地图范围（西太平洋）
    ax.set_extent([100, 160, 0, 50], crs=ccrs.PlateCarree())
    
    # 添加地图要素
    ax.add_feature(cfeature.COASTLINE, linewidth=0.8)
    ax.add_feature(cfeature.BORDERS, linestyle=":", linewidth=0.5)
    ax.add_feature(cfeature.OCEAN, color='lightblue', alpha=0.3)
    ax.add_feature(cfeature.LAND, color='lightgray', alpha=0.3)
    ax.gridlines(draw_labels=True, alpha=0.5)
    
    # 为每个台风绘制轨迹
    colors = plt.cm.viridis(np.linspace(0, 1, len(selected_storms)))
    
    for i, storm_id in enumerate(selected_storms):
        storm_data = storms[storms['SID'] == storm_id].copy()
        storm_data = storm_data.sort_values('ISO_TIME')  # 按时间排序
        
        if len(storm_data) < 2:  # 跳过数据点太少的台风
            continue
            
        # 绘制轨迹线
        ax.plot(storm_data['LON'], storm_data['LAT'], 
                color=colors[i], linewidth=2, alpha=0.7,
                transform=ccrs.PlateCarree(),
                label=f"{storm_data['NAME'].iloc[0]} ({storm_data['SEASON'].iloc[0]})")
        
        # 按风速着色散点
        scatter = ax.scatter(storm_data['LON'], storm_data['LAT'],
                           c=storm_data['WMO_WIND'], 
                           cmap='plasma', s=30, alpha=0.8,
                           transform=ccrs.PlateCarree())
    
    # 添加颜色条
    cbar = plt.colorbar(scatter, orientation="vertical", shrink=0.6, pad=0.05)
    cbar.set_label("Wind Speed (knots)", fontsize=12)
    
    # 添加图例
    ax.legend(loc='upper right', fontsize=10)
    
    plt.title("Typhoon Tracks in Western Pacific (2000+)", fontsize=14, fontweight='bold')
    plt.tight_layout()
    
    return plt

def plot_single_typhoon(storms, storm_index=0):
    """绘制单个台风的详细轨迹"""
    unique_storms = storms['SID'].unique()
    if storm_index >= len(unique_storms):
        storm_index = 0
    
    storm_id = unique_storms[storm_index]
    storm_data = storms[storms['SID'] == storm_id].copy()
    storm_data = storm_data.sort_values('ISO_TIME')
    
    print(f"绘制台风: {storm_data['NAME'].iloc[0]} ({storm_data['SEASON'].iloc[0]})")
    print(f"数据点数量: {len(storm_data)}")
    print(f"最大风速: {storm_data['WMO_WIND'].max():.1f} knots")
    
    # 创建图形
    plt.figure(figsize=(12, 8))
    ax = plt.axes(projection=ccrs.PlateCarree())
    
    # 设置地图范围
    ax.set_extent([100, 160, 0, 50], crs=ccrs.PlateCarree())
    
    # 添加地图要素
    ax.add_feature(cfeature.COASTLINE, linewidth=1)
    ax.add_feature(cfeature.BORDERS, linestyle=":", linewidth=0.8)
    ax.add_feature(cfeature.OCEAN, color='lightblue', alpha=0.3)
    ax.add_feature(cfeature.LAND, color='lightgray', alpha=0.3)
    ax.gridlines(draw_labels=True, alpha=0.5)
    
    # 绘制轨迹线
    ax.plot(storm_data['LON'], storm_data['LAT'], 
            color='red', linewidth=3, alpha=0.8,
            transform=ccrs.PlateCarree())
    
    # 按风速着色散点
    scatter = ax.scatter(storm_data['LON'], storm_data['LAT'],
                       c=storm_data['WMO_WIND'], 
                       cmap='plasma', s=60, alpha=0.9,
                       transform=ccrs.PlateCarree())
    
    # 标记起点和终点
    ax.scatter(storm_data['LON'].iloc[0], storm_data['LAT'].iloc[0], 
              color='green', s=100, marker='o', 
              transform=ccrs.PlateCarree(), label='Start')
    ax.scatter(storm_data['LON'].iloc[-1], storm_data['LAT'].iloc[-1], 
              color='red', s=100, marker='s', 
              transform=ccrs.PlateCarree(), label='End')
    
    # 添加颜色条
    cbar = plt.colorbar(scatter, orientation="vertical", shrink=0.6, pad=0.05)
    cbar.set_label("Wind Speed (knots)", fontsize=12)
    
    # 添加图例
    ax.legend(loc='upper right', fontsize=12)
    
    plt.title(f"Typhoon Track: {storm_data['NAME'].iloc[0]} ({storm_data['SEASON'].iloc[0]})", 
              fontsize=14, fontweight='bold')
    plt.tight_layout()
    
    return plt

def main():
    """主函数"""
    # 获取数据文件路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(current_dir, 'sample_typhoons.csv')
    
    if not os.path.exists(csv_path):
        print(f"错误: 找不到数据文件 {csv_path}")
        return
    
    try:
        # 加载数据
        storms = load_typhoon_data(csv_path)
        
        if len(storms) == 0:
            print("错误: 没有找到有效的台风数据")
            return
        
        # 显示选项
        print("\n选择可视化方式:")
        print("1. 显示多个台风轨迹")
        print("2. 显示单个台风详细轨迹")
        
        choice = input("请输入选择 (1 或 2, 默认1): ").strip()
        
        if choice == '2':
            # 显示单个台风
            storm_index = int(input(f"请输入台风索引 (0-{storms['SID'].nunique()-1}, 默认0): ") or "0")
            plt = plot_single_typhoon(storms, storm_index)
        else:
            # 显示多个台风
            num_tracks = int(input("请输入要显示的台风数量 (默认5): ") or "5")
            plt = plot_typhoon_tracks(storms, num_tracks)
        
        # 显示图形
        plt.show()
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
