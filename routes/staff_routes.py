# routes/staff_routes.py
# StaffRoutes - Manage Staff (owner only): list, add, edit and remove cashiers and chefs.

from flask import Blueprint, flash, redirect, render_template, request, url_for
from routes.auth_routes import roles_required
from services.staff_service import StaffService

staff_routes = Blueprint('staff_routes', __name__)


@staff_routes.get('/staff')
@roles_required('owner')
def staff_list():
    return render_template('staff.html', staff=StaffService.list_staff())


@staff_routes.route('/staff/new', methods=['GET', 'POST'])
@roles_required('owner')
def new_staff():
    if request.method == 'POST':
        try:
            user = StaffService.add_staff(request.form)
            flash(f'{user.role.capitalize()} account "{user.username}" was created.', 'success')
            return redirect(url_for('staff_routes.staff_list'))
        except ValueError as error:
            flash(str(error), 'danger')
    return render_template('staff_form.html', form=request.form, user=None)


@staff_routes.route('/staff/<int:user_id>/edit', methods=['GET', 'POST'])
@roles_required('owner')
def edit_staff(user_id):
    try:
        user = StaffService.get_staff(user_id)
    except ValueError as error:
        flash(str(error), 'danger')
        return redirect(url_for('staff_routes.staff_list'))
    if request.method == 'POST':
        try:
            StaffService.edit_staff(user_id, request.form)
            flash(f'Account "{user.username}" was updated.', 'success')
            return redirect(url_for('staff_routes.staff_list'))
        except ValueError as error:
            flash(str(error), 'danger')
            return render_template('staff_form.html', form=request.form, user=user)
    return render_template('staff_form.html', form={'username': user.username, 'role': user.role}, user=user)


@staff_routes.post('/staff/<int:user_id>/remove')
@roles_required('owner')
def remove_staff(user_id):
    try:
        user = StaffService.remove_staff(user_id)
        flash(f'Account "{user.username}" was removed. It can no longer log in.', 'success')
    except ValueError as error:
        flash(str(error), 'danger')
    return redirect(url_for('staff_routes.staff_list'))
