from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Any, List

import pandas as pd
from arcgis.gis import GIS
from arcgis.features import FeatureLayer  # used arcgis.features module


@dataclass(frozen=True)
class ArcGisConfig:
    url: str
    username: str
    password: str
    item_id: str


def _parse_coord(value: Any) -> float:
    """
    Перетворює координату (long/lat) у float.
    Підтримує десяткову кому (наприклад '30,7306393').
    """
    if value is None:
        raise ValueError("Координата порожня (None)")

    if isinstance(value, str):
        value = value.strip().replace(",", ".")
        if value == "":
            raise ValueError("Координата порожня (порожній рядок)")

    return float(value)


def _parse_uk_date_to_epoch_ms(date_str: str) -> int:
    """
    Перетворює дату у форматі 'DD.MM.YYYY' в мілісекунди від Unix epoch (UTC).
    """
    dt = datetime.strptime(date_str, "%d.%m.%Y").replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


def _build_field_mapping() -> Dict[str, str]:
    """
    Маппінг: назва колонки у DataFrame -> назва поля у Feature Layer.
    """
    return {
        "Дата": "d_date",
        "Область": "t_region",
        "Місто": "t_city",
        "Значення 1": "i_value_1",
        "Значення 2": "i_value_2",
        "Значення 3": "i_value_3",
        "Значення 4": "i_value_4",
        "Значення 5": "i_value_5",
        "Значення 6": "i_value_6",
        "Значення 7": "i_value_7",
        "Значення 8": "i_value_8",
        "Значення 9": "i_value_9",
        "Значення 10": "i_value_10",
    }


def _df_to_features(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Конвертує DataFrame в список features для ArcGIS:
    - attributes: значення полів
    - geometry: точка з координатами long/lat (WGS84, wkid=4326)
    """
    mapping = _build_field_mapping()

    features: List[Dict[str, Any]] = []

    for idx, row in enumerate(df.to_dict(orient="records"), start=1):
        try:
            # Геометрія
            x = _parse_coord(row["long"])
            y = _parse_coord(row["lat"])
        except Exception as e:
            print(
                f"Пропущено рядок #{idx}: некоректні координати long/lat. Причина: {e}"
            )
            continue

        geometry = {
            "x": x,
            "y": y,
            "spatialReference": {"wkid": 4326},
        }

        # Атрибути (поля)
        attributes: Dict[str, Any] = {}
        for df_col, layer_field in mapping.items():
            if df_col not in row:
                continue

            value = row[df_col]

            # Дату конвертуємо в epoch ms
            if df_col == "Дата":
                attributes[layer_field] = _parse_uk_date_to_epoch_ms(str(value))
            else:
                attributes[layer_field] = value

        features.append({"attributes": attributes, "geometry": geometry})

    return features


def _print_item_details_and_resources(item) -> None:
    """
    Друкує властивості Item та приклад доступу до його ресурсів.
    """
    print(f"Item title: {item.title}")
    print(f"Item type: {item.type}")
    print(f"Item owner: {item.owner}")

    # Accessing Item Resources (може бути порожнім у тестових шарах)
    try:
        resources = item.resources.list()
        print(f"Item resources count: {len(resources)}")
    except Exception as e:
        print(f"Не вдалося отримати item.resources: {e}")


def upload_dataframe_to_feature_layer(
    df: pd.DataFrame, cfg: ArcGisConfig, layer_index: int = 0
) -> None:
    """
    Завантажує підготовлений DataFrame у Hosted Feature Layer (ArcGIS Online).
    """
    gis = GIS(cfg.url, cfg.username, cfg.password)

    item = gis.content.get(cfg.item_id)
    if item is None:
        raise RuntimeError(f"Не знайдено Item за id: {cfg.item_id}")

    _print_item_details_and_resources(item)

    # Hosted Feature Layer може мати кілька шарів; беремо потрібний за індексом
    flayers = item.layers
    if not flayers or layer_index >= len(flayers):
        raise RuntimeError("У Item немає layer'ів або layer_index некоректний")

    layer = FeatureLayer(flayers[layer_index].url, gis=gis)

    print(f"Layer URL: {layer.url}")
    print(f"Geometry type: {layer.properties.get('geometryType')}")
    print(f"Capabilities: {layer.properties.get('capabilities')}")

    features = _df_to_features(df)

    # Відправляємо пачками (щоб не впертися в ліміти запиту)
    batch_size = 200
    for start in range(0, len(features), batch_size):
        chunk = features[start : start + batch_size]
        result = layer.edit_features(adds=chunk)

        # 1) Якщо ArcGIS повернув помилку на рівні запиту (а не по кожному feature)
        if isinstance(result, dict) and "error" in result:
            err = result["error"]
            print("Помилка ArcGIS edit_features:")
            print(f"  code: {err.get('code')}")
            print(f"  message: {err.get('message')}")
            details = err.get("details")
            if details:
                print(f"  details: {details}")
            # Далі немає сенсу продовжувати наступні батчі
            break

        # 2) Нормальний випадок: успіх/помилки по кожному доданому feature
        add_results = result.get("addResults", [])
        if not add_results:
            print(f"Немає addResults у відповіді. Повна відповідь: {result}")
            break

        ok = sum(1 for r in add_results if r.get("success"))
        fail = sum(1 for r in add_results if not r.get("success"))

        # Якщо є помилки — виведемо перші кілька, щоб зрозуміти причину
        if fail:
            first_errors = [r for r in add_results if not r.get("success")][:3]
            print(f"Приклад помилок (до 3): {first_errors}")

        print(f"Додано: {ok}, помилок: {fail} (batch {start // batch_size + 1})")

        # Демонстрація оновлення (Updating features):
        # Якщо хоча б один об'єкт додано успішно — оновимо перший.
        if ok > 0:
            first_success = next(r for r in add_results if r.get("success"))
            oid = first_success.get("objectId")

            # Оновлюємо тільки атрибут (геометрію не чіпаємо)
            updates = [{"attributes": {"OBJECTID": oid, "city": "updated_by_script"}}]
            upd_result = layer.edit_features(updates=updates)

            upd_ok = sum(
                1 for r in upd_result.get("updateResults", []) if r.get("success")
            )
            upd_fail = sum(
                1 for r in upd_result.get("updateResults", []) if not r.get("success")
            )
            print(f"Оновлено: {upd_ok}, помилок оновлення: {upd_fail}")
