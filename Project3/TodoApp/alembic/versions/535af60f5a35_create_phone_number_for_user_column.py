"""Create phone number for user column

Revision ID: 535af60f5a35
Revises: 
Create Date: 2024-10-11 15:43:12.303369

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '535af60f5a35'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('phone_number', sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'phone_number')
