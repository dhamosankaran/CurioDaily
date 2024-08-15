"""Update models and relationships

Revision ID: a99d00c9a9d1
Revises: 2b731c621d5f
Create Date: 2024-08-14 13:18:20.838456

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a99d00c9a9d1'
down_revision: Union[str, None] = '2b731c621d5f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
