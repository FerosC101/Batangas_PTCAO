<<<<<<< HEAD
from extension import db
from model import User
from app import create_app  # Import your app factory
import bcrypt
=======
# Create a new migration file (e.g., migrations/versions/XXXX_add_property_sequence.py)
from alembic import op
import sqlalchemy as sa
>>>>>>> af1d5da10b244ec5180bff12f15d972f0ddbfc4f

def upgrade():
    op.execute("CREATE SEQUENCE property_id_seq")
    op.execute("ALTER TABLE property ALTER COLUMN property_id SET DEFAULT nextval('property_id_seq')")
    op.execute("SELECT setval('property_id_seq', COALESCE((SELECT MAX(property_id) FROM property), 1))")

def downgrade():
    op.execute("ALTER TABLE property ALTER COLUMN property_id DROP DEFAULT")
    op.execute("DROP SEQUENCE property_id_seq")