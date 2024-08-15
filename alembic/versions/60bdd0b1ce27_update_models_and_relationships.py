# 60bdd0b1ce27_update_models_and_relationships.py

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision = '60bdd0b1ce27'
down_revision = 'a99d00c9a9d1'  # replace with the previous revision id
branch_labels = None
depends_on = None

def table_exists(table_name):
    inspector = Inspector.from_engine(op.get_bind())
    return table_name in inspector.get_table_names()

def upgrade():
    # Conditionally drop tables
    if table_exists('user_topic'):
        op.drop_table('user_topic')
    if table_exists('subscription_topic'):
        op.drop_table('subscription_topic')
    if table_exists('subscriptions'):
        op.drop_table('subscriptions')
    if table_exists('newsletters'):
        op.drop_table('newsletters')
    if table_exists('topics'):
        op.drop_table('topics')
    if table_exists('users'):
        op.drop_table('users')
    
    # Create tables
    op.create_table('topics',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_topics_id'), 'topics', ['id'], unique=False)
    op.create_index(op.f('ix_topics_name'), 'topics', ['name'], unique=True)
    
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('email', sa.String(), nullable=True),
    sa.Column('hashed_password', sa.String(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    
    op.create_table('newsletters',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(), nullable=True),
    sa.Column('content', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('topic_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['topic_id'], ['topics.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_newsletters_id'), 'newsletters', ['id'], unique=False)
    op.create_index(op.f('ix_newsletters_title'), 'newsletters', ['title'], unique=False)
    
    op.create_table('subscriptions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('email', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_subscriptions_email'), 'subscriptions', ['email'], unique=True)
    op.create_index(op.f('ix_subscriptions_id'), 'subscriptions', ['id'], unique=False)
    
    op.create_table('subscription_topic',
    sa.Column('subscription_id', sa.Integer(), nullable=True),
    sa.Column('topic_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['subscription_id'], ['subscriptions.id'], ),
    sa.ForeignKeyConstraint(['topic_id'], ['topics.id'], )
    )
    
    op.create_table('user_topic',
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('topic_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['topic_id'], ['topics.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], )
    )

def downgrade():
    op.drop_table('user_topic')
    op.drop_table('subscription_topic')
    op.drop_index(op.f('ix_subscriptions_id'), table_name='subscriptions')
    op.drop_index(op.f('ix_subscriptions_email'), table_name='subscriptions')
    op.drop_table('subscriptions')
    op.drop_index(op.f('ix_newsletters_title'), table_name='newsletters')
    op.drop_index(op.f('ix_newsletters_id'), table_name='newsletters')
    op.drop_table('newsletters')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    op.drop_index(op.f('ix_topics_name'), table_name='topics')
    op.drop_index(op.f('ix_topics_id'), table_name='topics')
    op.drop_table('topics')