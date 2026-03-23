#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Inicializacao centralizada do Firebase Admin para o backend do C.O.R.A.
"""

import os
import json
from functools import lru_cache
from pathlib import Path

import firebase_admin
from dotenv import load_dotenv
from firebase_admin import credentials, firestore
from google.auth import default as google_auth_default
from google.auth.exceptions import DefaultCredentialsError

load_dotenv(Path(__file__).resolve().parent / '.env')


@lru_cache(maxsize=1)
def get_firebase_app():
    if firebase_admin._apps:
        return firebase_admin.get_app()

    service_account_json = os.getenv('FIREBASE_SERVICE_ACCOUNT_JSON')
    service_account_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH')

    credential = None

    if service_account_json:
        try:
            service_account_data = json.loads(service_account_json)
        except json.JSONDecodeError as exc:
            raise RuntimeError('FIREBASE_SERVICE_ACCOUNT_JSON invalido') from exc
        credential = credentials.Certificate(service_account_data)
    elif service_account_path:
        service_account_file = Path(service_account_path)
        if not service_account_file.exists():
            raise RuntimeError(f'Arquivo de service account nao encontrado: {service_account_path}')

        credential = credentials.Certificate(str(service_account_file))
    else:
        try:
            google_auth_default()
        except DefaultCredentialsError as exc:
            raise RuntimeError(
                'FIREBASE_SERVICE_ACCOUNT_PATH ou FIREBASE_SERVICE_ACCOUNT_JSON nao configurado, '
                'e as credenciais padrao do Google nao estao disponiveis'
            ) from exc

    project_id = (
        os.getenv('FIREBASE_PROJECT_ID')
        or os.getenv('GOOGLE_CLOUD_PROJECT')
        or os.getenv('GCP_PROJECT')
    )
    storage_bucket = os.getenv('FIREBASE_STORAGE_BUCKET')

    options = {}
    if project_id:
        options['projectId'] = project_id
    if storage_bucket:
        options['storageBucket'] = storage_bucket

    return firebase_admin.initialize_app(credential, options or None)


@lru_cache(maxsize=1)
def get_firestore_client():
    app = get_firebase_app()
    return firestore.client(app=app)
