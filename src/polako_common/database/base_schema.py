from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase


class BaseSchema(DeclarativeBase):
    metadata = MetaData(naming_convention={
        "pk": "pk_%(table_name)s",  # primary key
        "ix": "ix_%(table_name)s_%(column_0_N_name)s",  # index
        "uq": "uq_%(table_name)s_%(column_0_N_name)s",  # unique index
        "fk": "fk_%(table_name)s_%(column_0_name)s__%(referred_table_name)s",  # foreign key
        "ck": "ck_%(table_name)s_%(constraint_name)s",  # check
    })
