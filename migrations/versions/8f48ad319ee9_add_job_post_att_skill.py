"""add job post att/skill

Revision ID: 8f48ad319ee9
Revises: e77705401a3f
Create Date: 2021-05-24 14:32:46.244518

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '8f48ad319ee9'
down_revision = 'e77705401a3f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('jobpost_attitude',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('jobpost_id', sa.Integer(), nullable=False),
    sa.Column('attitude_id', sa.Integer(), nullable=False),
    sa.Column('importance_level', postgresql.ENUM('none', 'vlow', 'low', 'mid', 'high', 'vhigh', name='importancelevel'), nullable=True),
    sa.ForeignKeyConstraint(['attitude_id'], ['attitude.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['jobpost_id'], ['jobpost.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('jobpost_skill',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('jobpost_id', sa.Integer(), nullable=False),
    sa.Column('skill_id', sa.Integer(), nullable=False),
    sa.Column('skill_level_min', postgresql.ENUM('novice', 'familiar', 'competent', 'proficient', 'expert', name='skilllevels', create_type=False), nullable=True),
    sa.Column('importance_level', postgresql.ENUM('none', 'vlow', 'low', 'mid', 'high', 'vhigh', name='importancelevel'), nullable=True),
    sa.ForeignKeyConstraint(['jobpost_id'], ['jobpost.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['skill_id'], ['skill.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('jobpost_skill')
    op.drop_table('jobpost_attitude')
    # ### end Alembic commands ###