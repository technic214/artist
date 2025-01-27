"""Updated models with Artist, Venue, and Show relationships

Revision ID: bfb82614952c
Revises: 5142ac660c0a
Create Date: 2025-01-27 22:00:09.015884

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bfb82614952c'
down_revision = '5142ac660c0a'
branch_labels = None
depends_on = None


def upgrade():
    # ### Recreate tables ###
    # Venues table
    op.create_table(
        'venues',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('city', sa.String(length=120), nullable=False),
        sa.Column('state', sa.String(length=120), nullable=False),
        sa.Column('address', sa.String(length=120), nullable=False),
        sa.Column('genres', sa.String(length=120), nullable=False),
        sa.Column('phone', sa.String(length=120), nullable=False),
        sa.Column('image_link', sa.String(length=500)),
        sa.Column('facebook_link', sa.String(length=120)),
        sa.Column('website_link', sa.String(length=120)),
        sa.Column('lookingfortalent', sa.Boolean(), nullable=False),
        sa.Column('seek', sa.String(length=120), nullable=False),
    )

    # Artists table
    op.create_table(
        'artists',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('city', sa.String(length=120)),
        sa.Column('state', sa.String(length=120)),
        sa.Column('phone', sa.String(length=120)),
        sa.Column('genres', sa.String(length=120)),
        sa.Column('image_link', sa.String(length=500)),
        sa.Column('facebook_link', sa.String(length=120)),
        sa.Column('website_link', sa.String(length=120)),
        sa.Column('lookingforVenue', sa.Boolean(), nullable=False),
        sa.Column('seek', sa.String(length=120), nullable=False),
    )

    # Shows table (many-to-many relationship)
    op.create_table(
        'shows',
        sa.Column('venue_id', sa.Integer(), sa.ForeignKey('venues.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('artist_id', sa.Integer(), sa.ForeignKey('artists.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('start_time', sa.DateTime(), nullable=False),
    )

    # ### end Alembic commands ###



def downgrade():
    # ## Drop all tables ###
    op.drop_table('venues')
    op.drop_table('artists')
    op.drop_table('shows')
