"""
Скачивает HYG v3, фильтрует mag ≤ 5.0 и сохраняет parquet.
Запуск: python scripts/fetch_hyg.py
После этого app автоматически использует parquet.
"""
import io
import urllib.request
from pathlib import Path

import pandas as pd

URL = ("https://raw.githubusercontent.com/astronexus/HYG-Database/"
       "main/hyg/v3/hyg_v37.csv.gz")
DST = Path(__file__).resolve().parent.parent / "sky_map" / "data" / "stars_hyg.parquet"


def main() -> None:
    DST.parent.mkdir(parents=True, exist_ok=True)
    print(f"Скачиваю {URL} …")
    with urllib.request.urlopen(URL, timeout=180) as r:
        data = r.read()
    df = pd.read_csv(io.BytesIO(data), compression="gzip")
    df = df.dropna(subset=["ra", "dec", "mag"])
    df = df[df["mag"] <= 5.0][["ra", "dec", "mag"]].copy()
    df.to_parquet(DST, index=False)
    print(f"Сохранено {len(df)} звёзд → {DST}")


if __name__ == "__main__":
    main()