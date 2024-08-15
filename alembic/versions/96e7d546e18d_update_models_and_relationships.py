"""Update models and relationships

Revision ID: 96e7d546e18d
Revises: 0b0763838d15
Create Date: 2024-08-14 11:53:38.055639

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '96e7d546e18d'
down_revision: Union[str, None] = '0b0763838d15'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
