"""Update models and relationships

Revision ID: 2b731c621d5f
Revises: 96e7d546e18d
Create Date: 2024-08-14 13:10:51.694696

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2b731c621d5f'
down_revision: Union[str, None] = '96e7d546e18d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
