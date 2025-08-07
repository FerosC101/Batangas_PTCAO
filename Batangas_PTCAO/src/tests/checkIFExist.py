# In Python shell with app context
from sqlalchemy import desc

from Batangas_PTCAO.src.model import Destination, Property

# Test destination query
destinations = Destination.query.order_by(desc(Destination.is_featured), Destination.name).all()
print([d.name for d in destinations])

# Test property query
properties = Property.query.filter(Property.status == 'ACTIVE').all()
print([p.property_name for p in properties])