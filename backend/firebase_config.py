#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Inicializacao centralizada do Firebase Admin para o backend do C.O.R.A.
"""

import os
from functools import lru_cache
from pathlib import Path

import firebase_admin
from dotenv import load_dotenv
from firebase_admin import credentials, firestore

load_dotenv(Path(__file__).resolve().parent / '.env')


@lru_cache(maxsize=1)
def get_firebase_app():
    if firebase_admin._apps:
        return firebase_admin.get_app()

    service_account_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH')
    if not service_account_path:
        raise RuntimeError('FIREBASE_SERVICE_ACCOUNT_PATH nao configurado')

    service_account_file = Path(service_account_path)
    if not service_account_file.exists():
        raise RuntimeError(f'Arquivo de service account nao encontrado: {service_account_path}')

    project_id = os.getenv('FIREBASE_PROJECT_ID')
    storage_bucket = os.getenv('FIREBASE_STORAGE_BUCKET')

    options = {}
    if project_id:
        options['projectId'] = project_id
    if storage_bucket:
        options['storageBucket'] = storage_bucket

    credential = credentials.Certificate(str(service_account_file))
    return firebase_admin.initialize_app(credential, options or None)


@lru_cache(maxsize=1)
def get_firestore_client():
    app = get_firebase_app()
    return firestore.client(app=app)
