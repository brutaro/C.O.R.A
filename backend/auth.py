#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Autenticacao Firebase para o backend do C.O.R.A.
"""

import logging
from pathlib import Path

from dotenv import load_dotenv
from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from firebase_admin import auth as firebase_auth

from firebase_config import get_firebase_app

load_dotenv(Path(__file__).resolve().parent / '.env')

logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=False)


async def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> dict:
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=401,
            detail='Token de autenticacao ausente.',
            headers={'WWW-Authenticate': 'Bearer'},
        )

    token = credentials.credentials

    try:
        firebase_app = get_firebase_app()
    except Exception as exc:
        logger.error('❌ Falha ao inicializar Firebase Admin para validacao do token: %s', exc)
        raise HTTPException(
            status_code=500,
            detail=f'Autenticacao Firebase do servidor indisponivel: {exc}',
        ) from exc

    try:
        payload = firebase_auth.verify_id_token(token, app=firebase_app)
    except Exception as exc:
        logger.error('❌ Falha ao validar token Firebase: %s', exc)
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
