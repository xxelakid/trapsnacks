# FR 7 Add a Rider
import pytest
from models import User
from services.new_rider_service import NewRiderService

GOOD = {'name': 'Damion Clarke', 'phone': '876-555-0104', 'address': '22 Red Hills Road',
        'trn': '456-789-123', 'email': 'damion@example.com', 'username': 'damion', 'password': 'secret1'}


def test_fr7_missing_field_is_named(app):
    data = dict(GOOD, trn='')
    with pytest.raises(ValueError, match='TRN'):
        NewRiderService.add_rider(data)


def test_fr7_complete_form_saves_rider_with_id_and_login(app):
    rider = NewRiderService.add_rider(GOOD)
    assert rider.id is not None
    assert User.query.filter_by(username='damion', rider_id=rider.id).first() is not None
