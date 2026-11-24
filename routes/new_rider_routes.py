# routes/new_rider_routes.py
# NewRiderRoutes - FR 7 Add a Rider.

from flask import Blueprint, flash, redirect, render_template, request, url_for
from routes.auth_routes import roles_required
from services.new_rider_service import NewRiderService

new_rider_routes = Blueprint('new_rider_routes', __name__)


@new_rider_routes.route('/riders/new', methods=['GET', 'POST'])
@roles_required('owner')
def new_rider():
    if request.method == 'POST':
        try:
            rider = NewRiderService.add_rider(request.form)
            flash(f'Rider {rider.name} was added (rider ID {rider.id}).', 'success')
            return redirect(url_for('remove_rider_routes.rider_list'))
        except ValueError as error:
            flash(str(error), 'danger')        # the form is shown again with what was typed
    return render_template('new_rider.html', form=request.form)
