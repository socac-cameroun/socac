#!/usr/bin/env python3
"""Sync private Google Sheet product prices into local prices.json for the SOCAC site.

How it works:
1) Create a Google Cloud service account.
2) Enable Google Sheets API in that project.
3) Share the private spreadsheet with the service-account email as Viewer.
4) Save the downloaded service-account JSON key locally.
5) Run this script to update prices.json.

Install once:
    pip install google-api-python-client google-auth

Examples:
    python sync_prices_from_private_sheet.py --credentials service-account.json
    python sync_prices_from_private_sheet.py --credentials service-account.json --spreadsheet-id 1DXIaKg5y0GtNOmi3PjWr-8-PnqQu9-k7
    python sync_prices_from_private_sheet.py --credentials service-account.json --sheet-range 'Feuille 1!A:H'
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import List, Dict, Any

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

DEFAULT_SPREADSHEET_ID = '1DXIaKg5y0GtNOmi3PjWr-8-PnqQu9-k7'
DEFAULT_SHEET_RANGE = 'A:Z'
ROOT_DIR = Path(__file__).resolve().parent
OUTPUT_FILE = ROOT_DIR / 'prices.json'
OUTPUT_JS_FILE = ROOT_DIR / 'prices-data.js'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

COLUMN_ALIASES = {
    'id': ['id', 'product_id', 'code'],
    'categorie': ['categorie', 'category', 'division', 'compartiment', 'section'],
    'nom': ['nom', 'name', 'produit', 'product'],
    'description': ['description', 'details', 'detail'],
    'prix': ['prix', 'price', 'tarif', 'montant'],
    'unite': ['unite', 'unit', 'unité'],
    'disponible': ['disponible', 'available', 'stock', 'availability'],
    'image': ['image', 'img', 'photo', 'photo_url', 'image_url'],
}


def normalize_header(header: str) -> str:
    return ''.join(ch.lower() for ch in header.strip() if ch.isalnum())


def match_column(headers: List[str], aliases: List[str]) -> int | None:
    normalized_headers = [normalize_header(h) for h in headers]
    normalized_aliases = [normalize_header(a) for a in aliases]
    for alias in normalized_aliases:
        if alias in normalized_headers:
            return normalized_headers.index(alias)
    return None


def value_at(row: List[str], index: int | None, default: str = '') -> str:
    if index is None or index >= len(row):
        return default
    return str(row[index]).strip()


def to_bool(value: str) -> bool:
    normalized = str(value).strip().lower()
    return normalized not in {'', '0', 'false', 'non', 'no', 'rupture', 'outofstock'}


def to_int(value: str) -> int:
    cleaned = ''.join(ch for ch in str(value) if ch.isdigit())
    return int(cleaned) if cleaned else 0


def fetch_rows(credentials_file: Path, spreadsheet_id: str, sheet_range: str) -> List[List[str]]:
    creds = Credentials.from_service_account_file(str(credentials_file), scopes=SCOPES)
    service = build('sheets', 'v4', credentials=creds)
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=sheet_range,
    ).execute()
    return result.get('values', [])


def rows_to_products(rows: List[List[str]]) -> List[Dict[str, Any]]:
    if not rows:
        raise ValueError('No rows returned from Google Sheets.')

    headers = rows[0]
    indexes = {key: match_column(headers, aliases) for key, aliases in COLUMN_ALIASES.items()}

    required = ['categorie', 'nom', 'prix']
    missing = [field for field in required if indexes[field] is None]
    if missing:
        raise ValueError(f'Missing required columns in sheet: {", ".join(missing)}')

    products: List[Dict[str, Any]] = []
    for row_number, row in enumerate(rows[1:], start=2):
        category = value_at(row, indexes['categorie'])
        name = value_at(row, indexes['nom'])
        if not category or not name:
            continue

        product_id = value_at(row, indexes['id']) or str(len(products) + 1)
        product = {
            'id': product_id,
            'category': category,
            'nom': name,
            'description': value_at(row, indexes['description']),
            'prix': to_int(value_at(row, indexes['prix'])),
            'unite': value_at(row, indexes['unite']),
            'disponible': to_bool(value_at(row, indexes['disponible'], 'true')),
            'image': value_at(row, indexes['image']),
        }
        products.append(product)

    if not products:
        raise ValueError('No usable products found after parsing the sheet.')
    return products


def main() -> None:
    parser = argparse.ArgumentParser(description='Sync private Google Sheet prices into prices.json')
    parser.add_argument('--credentials', required=True, help='Path to the Google service-account JSON key')
    parser.add_argument('--spreadsheet-id', default=os.getenv('SOCAC_SPREADSHEET_ID', DEFAULT_SPREADSHEET_ID))
    parser.add_argument('--sheet-range', default=os.getenv('SOCAC_SHEET_RANGE', DEFAULT_SHEET_RANGE))
    parser.add_argument('--output', default=str(OUTPUT_FILE), help='Output prices.json path')
    args = parser.parse_args()

    credentials_file = Path(args.credentials).expanduser().resolve()
    if not credentials_file.exists():
        raise FileNotFoundError(f'Credentials file not found: {credentials_file}')

    rows = fetch_rows(credentials_file, args.spreadsheet_id, args.sheet_range)
    products = rows_to_products(rows)

    output_file = Path(args.output).expanduser().resolve()
    output_file.write_text(json.dumps(products, ensure_ascii=False, indent=2), encoding='utf-8')

    output_js_file = output_file.with_name('prices-data.js')
    output_js_file.write_text('window.SOCAC_PRICES = ' + json.dumps(products, ensure_ascii=False, separators=(',', ':')) + ';\n', encoding='utf-8')

    print(f'Updated {output_file} and {output_js_file} with {len(products)} products.')
    print('Next step: upload/deploy the updated prices.json and prices-data.js files with your website files.')


if __name__ == '__main__':
    main()
