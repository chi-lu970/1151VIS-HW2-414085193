"""
下載 CHIRPS v3.0 的 2025 年逐月降雨量（0.05° ≈ 5 km，衛星估計 + 測站觀測融合），
重採樣到與 taiwan-dem-grid.json 完全相同的網格，輸出兩份 D3.js 可直接讀取的 JSON。

資料來源：https://www.chc.ucsb.edu/data/chirps3
全球檔每月約數十 MB，這裡用 GDAL 的 /vsicurl/ 只讀台灣範圍，不必整檔下載；
讀到的台灣範圍會快取在 data/raw/rain/（不進 git）。

處理流程：
1. 讀 taiwan-dem-grid.json，取得網格定義與本島遮罩（必須先跑過 process_dem.py）
2. 逐月讀取台灣範圍的降雨量
3. 來源的海洋像元是 nodata，先用最近的有值像元補上，避免沿海格內插到空值
4. 雙線性內插到顯示網格的每個格心，套用本島遮罩
   → rain-grid.json
5. 依 DEM 的高程帶統計各月平均降雨量（依緯度做面積加權）
   → rain-by-band.json
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import rasterio
from rasterio.windows import from_bounds, transform as window_transform
from scipy import ndimage

ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = ROOT / "data" / "raw" / "rain"
OUT_DIR = ROOT / "public" / "data"

YEAR = 2025
BASE_URL = "https://data.chc.ucsb.edu/products/CHIRPS/v3.0/monthly/global/tifs"
SOURCE = f"CHIRPS v3.0 monthly precipitation, {YEAR}, 0.05 degree"

ELEVATION_BANDS_M = [0, 100, 500, 1000, 1500, 2000, 2500, 3000, 3500, 10000]
NODATA_OUT = -1  # 降雨量不會是負的，用 -1 標記海洋／離島，檔案比較小
PAD_DEG = 0.1    # 讀取範圍比 bbox 多留一圈，內插邊緣格心時才有鄰居


def read_month(month: int, bbox: list[float]) -> tuple[np.ndarray, rasterio.Affine]:
    """回傳某月台灣範圍的降雨量陣列（nodata 為 NaN）與其仿射轉換。"""
    cache = CACHE_DIR / f"chirps_{YEAR}_{month:02d}.tif"
    if not cache.exists():
        url = f"/vsicurl/{BASE_URL}/chirps-v3.0.{YEAR}.{month:02d}.tif"
        lon_min, lat_min, lon_max, lat_max = bbox
        with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR"):
            with rasterio.open(url) as src:
                window = from_bounds(
                    lon_min - PAD_DEG, lat_min - PAD_DEG,
                    lon_max + PAD_DEG, lat_max + PAD_DEG,
                    src.transform,
                ).round_offsets().round_lengths()
                data = src.read(1, window=window)
                profile = src.profile | dict(
                    width=data.shape[1],
                    height=data.shape[0],
                    transform=window_transform(window, src.transform),
                    blockysize=1,
                )
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        with rasterio.open(cache, "w", **profile) as dst:
            dst.write(data, 1)
        print(f"downloaded: {cache.name}")

    with rasterio.open(cache) as src:
        data = src.read(1).astype(np.float64)
        data[data < 0] = np.nan  # CHIRPS 海洋為 -9999，檔案沒有設定 nodata
        return data, src.transform


def fill_nodata_nearest(array: np.ndarray) -> np.ndarray:
    missing = np.isnan(array)
    idx = ndimage.distance_transform_edt(missing, return_distances=False, return_indices=True)
    return array[tuple(idx)]


def main() -> None:
    dem_path = OUT_DIR / "taiwan-dem-grid.json"
    if not dem_path.exists():
        raise SystemExit(f"找不到 {dem_path}，請先執行 process_dem.py")
    dem = json.loads(dem_path.read_text(encoding="utf-8"))
    width, height, bbox = dem["width"], dem["height"], dem["bbox"]
    lon_min, lat_min, lon_max, lat_max = bbox
    elev = np.array(dem["values"]).reshape(height, width)
    island = elev != dem["nodata"]

    # 顯示網格每個格心的經緯度（row 0 = 最北緣）
    lons = lon_min + (np.arange(width) + 0.5) * (lon_max - lon_min) / width
    lats = lat_max - (np.arange(height) + 0.5) * (lat_max - lat_min) / height
    lon_grid, lat_grid = np.meshgrid(lons, lats)

    months = []
    for month in range(1, 13):
        rain, transform = read_month(month, bbox)
        rain = fill_nodata_nearest(rain)
        # 經緯度 → 來源陣列的 (row, col)；減 0.5 是因為像元值代表像元中心
        cols, rows = ~transform * (lon_grid, lat_grid)
        sampled = ndimage.map_coordinates(rain, [rows - 0.5, cols - 0.5], order=1, mode="nearest")
        months.append(np.where(island, np.rint(sampled), NODATA_OUT).astype(int))

    rain_grid = {
        "width": width,
        "height": height,
        "bbox": bbox,
        "nodata": NODATA_OUT,
        "unit": "mm / month",
        "year": YEAR,
        "source": SOURCE,
        "note": "網格與 taiwan-dem-grid.json 相同；months[0] = 一月",
        "months": [m.flatten().tolist() for m in months],
    }

    # 各高程帶的月平均降雨量；同一列的格子面積相同，權重只跟緯度有關
    weights = np.cos(np.radians(lat_grid))
    bands = []
    for lo, hi in zip(ELEVATION_BANDS_M[:-1], ELEVATION_BANDS_M[1:]):
        in_band = island & (elev >= lo) & (elev < hi)
        bands.append(
            {
                "min_m": lo,
                "max_m": None if hi == ELEVATION_BANDS_M[-1] else hi,
                "rain_mm": [
                    round(float(np.average(m[in_band], weights=weights[in_band])), 1)
                    for m in months
                ],
            }
        )
    rain_by_band = {
        "unit": "mm / month",
        "year": YEAR,
        "source": SOURCE,
        "island_mean_mm": [
            round(float(np.average(m[island], weights=weights[island])), 1) for m in months
        ],
        "bands": bands,
    }

    (OUT_DIR / "rain-grid.json").write_text(
        json.dumps(rain_grid, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
    )
    (OUT_DIR / "rain-by-band.json").write_text(
        json.dumps(rain_by_band, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print("\n完成，輸出：")
    print(f"  {OUT_DIR / 'rain-grid.json'}")
    print(f"  {OUT_DIR / 'rain-by-band.json'}")
    print("\n本島各月平均降雨量 (mm)：", rain_by_band["island_mean_mm"])


if __name__ == "__main__":
    main()
