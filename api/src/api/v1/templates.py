from model import Template
from schema import Event, Template_schema
from db.psql import get_session
from sqlalchemy.ext.asyncio import AsyncSession

import http
import logging

from fastapi import APIRouter, Depends, HTTPException


logger = logging.getLogger('uvicorn')
router = APIRouter()

@router.post('', status_code=http.HTTPStatus.CREATED)
async def add_template(data: Template_schema, db_session: AsyncSession = Depends(get_session)):
    try:
        await Template(data).add_template(db_session)
    except Exception as err:
        logger.error(f'ERROR - cant create template: {str(err)}')
        raise HTTPException(
            http.HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=f'{http.HTTPStatus.INTERNAL_SERVER_ERROR}: Internal server error. Please try later.',
        )
    return {http.HTTPStatus.CREATED: 'Template has been created'}


@router.get('', status_code=http.HTTPStatus.OK)
async def get_template(db_session: AsyncSession = Depends(get_session)):
    data = await Template.get_templates(db_session)
    return data
