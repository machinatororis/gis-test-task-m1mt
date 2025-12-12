from pathlib import Path
import pandas as pd

from transform import expand_rows_df


def main():
    # Шлях до data/input.csv відносно цього файлу (src/main.py)
    csv_path = Path(__file__).resolve().parents[1] / "data" / "input.csv"

    # читаємо CSV → DataFrame
    df = pd.read_csv(csv_path)

    # Перетворюємо дані
    expanded_df = expand_rows_df(df)

    print(f"Input rows: {len(df)}")
    print(f"Expanded rows: {len(expanded_df)}")
    print(expanded_df.head(10))


if __name__ == "__main__":
    main()
