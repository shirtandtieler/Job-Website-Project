"""add seeker history

Revision ID: 955c3aaae008
Revises: 134ed68b09cf
Create Date: 2021-05-24 13:38:10.803157

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '955c3aaae008'
down_revision = '134ed68b09cf'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('seeker_history_education',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('seeker_id', sa.Integer(), nullable=False),
    sa.Column('school', sa.String(), nullable=False),
    sa.Column('education_lvl', postgresql.ENUM('certification', 'associate', 'bachelor', 'master', 'doctoral', name='educationlevel'), nullable=False),
    sa.Column('study_field', sa.String(), nullable=False),
    sa.ForeignKeyConstraint(['seeker_id'], ['seeker_profile.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('seeker_history_job',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('seeker_id', sa.Integer(), nullable=False),
    sa.Column('job_title', sa.String(length=191), nullable=True),
    sa.Column('years_employed', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['seeker_id'], ['seeker_profile.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('seeker_history_job')
    op.drop_table('seeker_history_education')
    # ### end Alembic commands ###