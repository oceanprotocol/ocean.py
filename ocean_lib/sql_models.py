#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from sqlalchemy import Column, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class AuthToken(Base):
    __tablename__ = "auth_tokens"

    address = Column(String(255), nullable=False, primary_key=True, autoincrement=False)
    signed_token = Column(String(255), nullable=False)
    created = Column(String(255), nullable=False)
