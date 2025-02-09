"""Пересоздание миграций

Revision ID: 11d60b328953
Revises: 
Create Date: 2025-02-03 23:19:50.886463

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '11d60b328953'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('schedule', schema=None) as batch_op:
        batch_op.add_column(sa.Column('date', sa.Date(), nullable=False))
        batch_op.alter_column('start_time',
               existing_type=sa.DATETIME(),
               type_=sa.Time(),
               existing_nullable=False)
        batch_op.alter_column('end_time',
               existing_type=sa.DATETIME(),
               type_=sa.Time(),
               existing_nullable=False)
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key(None, 'teacher', ['teacher_id'], ['teacher_id'])
        batch_op.drop_column('start_date')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('schedule', schema=None) as batch_op:
        batch_op.add_column(sa.Column('start_date', sa.DATE(), nullable=True))
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key(None, 'teacher', ['teacher_id'], ['id'])
        batch_op.alter_column('end_time',
               existing_type=sa.Time(),
               type_=sa.DATETIME(),
               existing_nullable=False)
        batch_op.alter_column('start_time',
               existing_type=sa.Time(),
               type_=sa.DATETIME(),
               existing_nullable=False)
        batch_op.drop_column('date')

    # ### end Alembic commands ###
