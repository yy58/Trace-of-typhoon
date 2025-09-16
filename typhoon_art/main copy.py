import pandas as pd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

# 1. 读取 IBTrACS 西北太平洋数据
url = "https://www.ncei.noaa.gov/data/international-best-track-archive-for-climate-stewardship-ibtracs/v04r00/access/csv/ibtracs.WP.list.v04r00.csv"
df = pd.read_csv(url, low_memory=False)

# 查看列名
print(df.columns[:20])

# 2. 基础清洗
# 只取部分字段：风暴 ID、名字、时间、经纬度、最大风速
storms = df[['SID', 'NAME', 'SEASON', 'ISO_TIME', 'LAT', 'LON', 'WMO_WIND']].dropna()

# 选择近年的（2000 年以后）
storms = storms[storms['SEASON'] >= 2000]

# 3. 画一个示例台风轨迹
example_sid = storms['SID'].unique()[100]  # 随便挑一个
storm_track = storms[storms['SID'] == example_sid]

# 4. 可视化轨迹
plt.figure(figsize=(10, 8))
ax = plt.axes(projection=ccrs.PlateCarree())
ax.set_extent([100, 160, 0, 50], crs=ccrs.PlateCarree())  # 西太平洋区域

# 添加底图要素
ax.add_feature(cfeature.COASTLINE)
ax.add_feature(cfeature.BORDERS, linestyle=":")
ax.gridlines(draw_labels=True)

# 按风速着色
sc = ax.scatter(
    storm_track['LON'], storm_track['LAT'],
    c=storm_track['WMO_WIND'],
    cmap="plasma", s=40, transform=ccrs.PlateCarree()
)

# 添加颜色条
cbar = plt.colorbar(sc, orientation="vertical", shrink=0.6, pad=0.05)
cbar.set_label("Wind Speed (knots)")

plt.title(f"Typhoon Track Example: {storm_track['NAME'].iloc[0]} ({storm_track['SEASON'].iloc[0]})")
plt.show()
