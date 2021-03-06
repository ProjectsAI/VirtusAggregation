"""configurations table

Revision ID: 3d62f809062c
Revises: fb4151d3ce55
Create Date: 2020-11-02 18:26:12.590846

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3d62f809062c'
down_revision = 'fb4151d3ce55'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('ix_configuration_confname', table_name='configuration')
    op.create_index(op.f('ix_configuration_confname'), 'configuration', ['confname'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_configuration_confname'), table_name='configuration')
    op.create_index('ix_configuration_confname', 'configuration', ['confname'], unique=1)
    # ### end Alembic commands ###
