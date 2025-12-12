from __future__ import annotations

from typing import Dict, List, Any


VALUE_COLS = [f"Значення {i}" for i in range(1, 11)]


def expand_row(row: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Перетворює один рядок вихідної таблиці на кілька рядків за правилом:

    - Якщо у якихось колонках "Значення X" стоїть число N > 0,
      ми повинні створити N рядків.
    - У кожному створеному рядку:
        * дата/регіон/місто/координати копіюються
        * "Значення X" перетворюються на 0/1 (бінарно)
    Причому якщо у різних колонках різні N, то:
    - всього рядків = max(N по всіх колонках)
    - для кожної колонки X:
      перші N рядків отримують 1, решта 0

    Приклад:
        v1 = 5, v2 = 3 -> всього 5 рядків
        v1: 1 1 1 1 1
        v2: 1 1 1 0 0
    """
    # Беремо лише позитивні значення із колонок "Значення 1..10"
    counts = {col: int(row.get(col, 0) or 0) for col in VALUE_COLS}

    total = max(counts.values(), default=0)

    base_fields = {k: v for k, v in row.items() if k not in VALUE_COLS}

    if total <= 0:
        new_row = dict(base_fields)
        for col in VALUE_COLS:
            new_row[col] = 0
        return [new_row]

    out: List[Dict[str, Any]] = []
    for i in range(total):
        new_row = dict(base_fields)
        for col in VALUE_COLS:
            new_row[col] = 1 if i < counts[col] else 0
        out.append(new_row)

    return out


def expand_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Застосовує expand_row для всіх рядків."""
    result: List[Dict[str, Any]] = []
    for row in rows:
        result.extend(expand_row(row))
    return result
