# routes/edit_rider_routes.py
# EditRiderRoutes - FR 8 Edit a Rider.

from flask import Blueprint, flash, redirect, render_template, request, url_for
from extensions import db
from models import Rider
from routes.auth_routes import roles_required
from services.edit_rider_service import EditRiderService

edit_rider_routes = Blueprint('edit_rider_routes', __name__)


@edit_rider_routes.route('/riders/<int:rider_id>/edit', methods=['GET', 'POST'])
@roles_required('owner')
def edit_rider(rider_id):
    rider = db.get_or_404(Rider, rider_id)
    if request.method == 'POST':
        try:
            EditRiderService.edit_rider(rider_id, request.form)
            flash(f'Rider {rider.name} was updated.', 'success')
            return redirect(url_for('remove_rider_routes.rider_list'))
        except ValueError as error:
            flash(str(error), 'danger')
            return render_template('edit_rider.html', rider=rider, form=request.form)
    form = {'name': rider.name, 'phone': rider.phone, 'address': rider.address,
            'trn': rider.trn, 'email': rider.email}
    return render_template('edit_rider.html', rider=rider, form=form)
