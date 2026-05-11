import re
import uuid
import pandas as pd
from sqlalchemy.orm import Session
from models import Product, init_db, engine

def normalize_text(text):
    if pd.isna(text):
        return None
    text = str(text).strip().lower()
    text = re.sub(r'[^\w\s]', '', text)
    return text

def import_csv(file_path, supplier_id, column_mapping=None):
    init_db()
    df = pd.read_csv(file_path)

    if column_mapping is None:
        column_mapping = {
            'name': 'product_name',
            'description': 'description',
            'category': 'category'
        }

    products = []
    with Session(engine) as session:
        for _, row in df.iterrows():
            original_name = str(row.get(column_mapping.get('name', 'product_name'), ''))
            normalized_name = normalize_text(original_name)
            description = str(row.get(column_mapping.get('description', 'description'), '')) if pd.notna(row.get(column_mapping.get('description', 'description'), '')) else '[MISSING]'
            category = str(row.get(column_mapping.get('category', 'category'), '')) if pd.notna(row.get(column_mapping.get('category', 'category'), '')) else None

            metadata = row.to_dict()
            metadata['_import_supplier'] = supplier_id

            product = Product(
                id=uuid.uuid4(),
                supplier_id=supplier_id,
                original_name=original_name,
                normalized_name=normalized_name,
                description=description,
                category=category if category and category != 'nan' else None,
                metadata=metadata
            )
            products.append(product)

        session.add_all(products)
        session.commit()

    return len(products)