# routes/remove_rider_routes.py
# RemoveRiderRoutes - FR 9 Remove a Rider (also shows the RiderListScreen).

from flask import Blueprint, flash, redirect, render_template, url_for
from models import Rider
from routes.auth_routes import roles_required
from services.remove_rider_service import RemoveRiderService

remove_rider_routes = Blueprint('remove_rider_routes', __name__)


@remove_rider_routes.get('/riders')
@roles_required('owner')
def rider_list():
    riders = Rider.query.filter_by(removed=False).order_by(Rider.name).all()
    return render_template('riders.html', riders=riders)


@remove_rider_routes.post('/riders/<int:rider_id>/remove')
@roles_required('owner')
def remove_rider(rider_id):
    try:
        rider = RemoveRiderService.remove_rider(rider_id)
        flash(f'Rider {rider.name} was removed.', 'success')
    except ValueError as error:
        flash(str(error), 'danger')
    return redirect(url_for('remove_rider_routes.rider_list'))
