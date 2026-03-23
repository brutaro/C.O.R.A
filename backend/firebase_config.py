#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Inicializacao centralizada do Firebase Admin para o backend do C.O.R.A.
"""

import json
import os
from functools import lru_cache
from pathlib import Path

import firebase_admin
from dotenv import load_dotenv
from firebase_admin import credentials, firestore
from google.auth import default as google_auth_default
from google.auth.exceptions import DefaultCredentialsError

load_dotenv(Path(__file__).resolve().parent / '.env')


DEFAULT_FIREBASE_PROJECT_ID = 'cora-9d120'


def get_default_project_id():
    return (
        os.getenv('FIREBASE_PROJECT_ID')
        or os.getenv('GOOGLE_CLOUD_PROJECT')
        or os.getenv('GCP_PROJECT')
        or DEFAULT_FIREBASE_PROJECT_ID
    )


def _build_firebase_credential():
    service_account_json = os.getenv('FIREBASE_SERVICE_ACCOUNT_JSON')
    service_account_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH')

    if service_account_json:
        try:
            service_account_data = json.loads(service_account_json)
        except json.JSONDecodeError as exc:
            raise RuntimeError('FIREBASE_SERVICE_ACCOUNT_JSON invalido') from exc
        return credentials.Certificate(service_account_data)

    if service_account_path:
        service_account_file = Path(service_account_path)
        if not service_account_file.exists():
            raise RuntimeError(f'Arquivo de service account nao encontrado: {service_account_path}')

        return credentials.Certificate(str(service_account_file))

    try:
        google_auth_default()
    except DefaultCredentialsError as exc:
        raise RuntimeError(
            'FIREBASE_SERVICE_ACCOUNT_PATH ou FIREBASE_SERVICE_ACCOUNT_JSON nao configurado, '
            'e as credenciais padrao do Google nao estao disponiveis'
        ) from exc

    return credentials.ApplicationDefault()


@lru_cache(maxsize=8)
def get_firebase_app(project_id: str | None = None):
    resolved_project_id = project_id or get_default_project_id()
    storage_bucket = os.getenv('FIREBASE_STORAGE_BUCKET')
    app_name = f'cora-{resolved_project_id}'

    try:
        return firebase_admin.get_app(app_name)
    except ValueError:
        pass

    options = {}
    if resolved_project_id:
        options['projectId'] = resolved_project_id
    if storage_bucket:
        options['storageBucket'] = storage_bucket

    credential = _build_firebase_credential()
    return firebase_admin.initialize_app(credential, options or None, name=app_name)


@lru_cache(maxsize=1)
def get_firestore_client():
    app = get_firebase_app()
    database_id = os.getenv('FIREBASE_FIRESTORE_DATABASE_ID')
    if database_id in {'', '(default)'}:
        database_id = None
    return firestore.client(app=app, database_id=database_id)
