# services/edit_rider_service.py
# EditRiderService - FR 8 Edit a Rider.

from extensions import db
from models import Rider
from services.new_rider_service import NewRiderService, FIELDS


class EditRiderService:
    @staticmethod
    def edit_rider(rider_id, data):
        rider = db.get_or_404(Rider, rider_id)
        if rider.removed:
            raise ValueError('This rider has been removed.')
        NewRiderService.validate_rider(data)          # same check as adding a rider
        for key, _ in FIELDS:
            setattr(rider, key, data[key].strip())
        db.session.commit()
        return rider
