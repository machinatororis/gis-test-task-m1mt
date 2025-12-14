from pathlib import Path
import pandas as pd
import os

from dotenv import load_dotenv
from transform import expand_rows_df
from arcgis_upload import ArcGisConfig, upload_dataframe_to_feature_layer


def main():
    load_dotenv()

    # Шлях до data/input.csv відносно цього файлу (src/main.py)
    csv_path = Path(__file__).resolve().parents[1] / "data" / "input.csv"

    # читаємо CSV → DataFrame
    df = pd.read_csv(csv_path)

    # Перетворюємо дані
    expanded_df = expand_rows_df(df)

    print(f"Input rows: {len(df)}")
    print(f"Expanded rows: {len(expanded_df)}")
    print(expanded_df.head(10))

    cfg = ArcGisConfig(
        url=os.environ.get("ARCGIS_URL", "https://www.arcgis.com"),
        username=os.environ["ARCGIS_USERNAME"],
        password=os.environ["ARCGIS_PASSWORD"],
        item_id=os.environ.get("ARCGIS_ITEM_ID", "c51cb411da1a468aaed719085337cc2b"),
    )

    upload_dataframe_to_feature_layer(expanded_df, cfg, layer_index=0)


if __name__ == "__main__":
    main()
