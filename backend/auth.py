#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Autenticacao Firebase para o backend do C.O.R.A.
"""

import base64
import json
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from firebase_admin import auth as firebase_auth

from firebase_config import DEFAULT_FIREBASE_PROJECT_ID, get_default_project_id, get_firebase_app

load_dotenv(Path(__file__).resolve().parent / '.env')

logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=False)


def _decode_token_claims_without_verification(token: str) -> dict:
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return {}
        payload = parts[1]
        padding = '=' * (-len(payload) % 4)
        decoded = base64.urlsafe_b64decode(payload + padding)
        data = json.loads(decoded.decode('utf-8'))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _get_allowed_project_ids() -> set[str]:
    allowed = {
        get_default_project_id(),
        DEFAULT_FIREBASE_PROJECT_ID,
    }

    raw_env = os.getenv('FIREBASE_ALLOWED_PROJECT_IDS', '')
    allowed.update(project_id.strip() for project_id in raw_env.split(',') if project_id.strip())
    return {project_id for project_id in allowed if project_id}


async def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> dict:
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=401,
            detail='Token de autenticacao ausente.',
            headers={'WWW-Authenticate': 'Bearer'},
        )

    token = credentials.credentials
    token_claims = _decode_token_claims_without_verification(token)
    token_project_id = token_claims.get('aud')
    allowed_project_ids = _get_allowed_project_ids()
    target_project_id = token_project_id if token_project_id in allowed_project_ids else get_default_project_id()

    try:
        firebase_app = get_firebase_app(target_project_id)
    except Exception as exc:
        logger.error('❌ Falha ao inicializar Firebase Admin para validacao do token: %s', exc)
        raise HTTPException(
            status_code=500,
            detail=f'Autenticacao Firebase do servidor indisponivel: {exc}',
        ) from exc

    try:
        payload = firebase_auth.verify_id_token(token, app=firebase_app)
    except Exception as exc:
        logger.error(
            '❌ Falha ao validar token Firebase: %s (%s) | token_aud=%s | target_project_id=%s | allowed_project_ids=%s',
            exc,
            exc.__class__.__name__,
            token_project_id,
            target_project_id,
            sorted(allowed_project_ids),
        )
        raise HTTPException(
            status_code=401,
            detail='Token de autenticacao invalido ou expirado. Faca login novamente.',
            headers={'WWW-Authenticate': 'Bearer'},
        ) from exc

    uid = payload.get('uid')
    if not uid:
        raise HTTPException(
            status_code=401,
            detail='Token invalido: usuario nao identificado.',
            headers={'WWW-Authenticate': 'Bearer'},
        )

    return {
        'uid': uid,
        'email': payload.get('email'),
        'name': payload.get('name'),
        'payload': payload,
    }
