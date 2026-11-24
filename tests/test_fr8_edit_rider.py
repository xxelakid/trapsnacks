# FR 8 Edit a Rider
import pytest
from services.edit_rider_service import EditRiderService
from services.new_rider_service import NewRiderService

GOOD = {'name': 'Damion Clarke', 'phone': '876-555-0104', 'address': '22 Red Hills Road',
        'trn': '456-789-123', 'email': 'damion@example.com', 'username': 'damion', 'password': 'secret1'}


def test_fr8_edit_saves_changes_and_checks_fields(app):
    rider = NewRiderService.add_rider(GOOD)
    EditRiderService.edit_rider(rider.id, dict(GOOD, phone='876-555-7777'))
    assert rider.phone == '876-555-7777'
    with pytest.raises(ValueError, match='Name'):
        EditRiderService.edit_rider(rider.id, dict(GOOD, name=''))
