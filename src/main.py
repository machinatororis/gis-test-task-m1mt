from sample_data import get_sample_rows
from transform import expand_rows


def main():
    rows = get_sample_rows()
    expanded = expand_rows(rows)

    print(f"Input rows: {len(rows)}")
    print(f"Expanded rows: {len(expanded)}")

    # Покажемо перші кілька рядків
    for idx, r in enumerate(expanded[:10], start=1):
        print(idx, r)


if __name__ == "__main__":
    main()
