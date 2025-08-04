# In your Python shell or a temporary route, run:
from Batangas_PTCAO.src.model import TouristReport, Property

# Check if any TouristReport records exist for your municipality
reports = TouristReport.query.join(Property).filter(Property.municipality == "YourMunicipalityName").all()
print(f"Found {len(reports)} TouristReport records")

# Check if any properties exist for your municipality
properties = Property.query.filter_by(municipality="YourMunicipalityName").all()
print(f"Found {len(properties)} Properties")