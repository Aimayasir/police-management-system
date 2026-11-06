from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from app.models.base import db
from app.models.resources import Vehicle, Weapon, InventoryItem
from app.models.station import PoliceStation
from app.forms.operational_forms import VehicleForm, WeaponForm
from app.utils.decorators import role_required
from app.utils.audit import log_audit

resources_bp = Blueprint('resources', __name__, url_prefix='/resources')

# ==================== VEHICLES ====================

@resources_bp.route('/vehicles', methods=['GET', 'POST'])
@login_required
def vehicles():
    form = VehicleForm()
    stations = PoliceStation.active().order_by(PoliceStation.name).all()
    form.station_id.choices = [(s.id, s.name) for s in stations]

    if form.validate_on_submit() and current_user.has_role('Admin', 'SHO'):
        try:
            existing = Vehicle.active().filter_by(registration_number=form.registration_number.data).first()
            if existing:
                flash(f"Vehicle with plate {form.registration_number.data} is already registered.", 'danger')
            else:
                vehicle = Vehicle(
                    station_id=form.station_id.data,
                    registration_number=form.registration_number.data,
                    vehicle_type=form.vehicle_type.data,
                    make_model=form.make_model.data,
                    year=form.year.data,
                    fuel_type=form.fuel_type.data,
                    operational_status=form.operational_status.data,
                    current_odometer_km=form.current_odometer_km.data,
                    created_by=current_user.id
                )
                db.session.add(vehicle)
                db.session.commit()
                log_audit('CREATE', 'vehicles', vehicle.id, description=f"Registered vehicle {vehicle.registration_number}")
                flash(f"Vehicle {vehicle.registration_number} registered successfully.", 'success')
                return redirect(url_for('resources.vehicles'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error registering vehicle: {str(e)}", 'danger')

    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str).strip()
    status = request.args.get('status', '', type=str).strip()

    query = Vehicle.active().order_by(Vehicle.id.desc())
    if search:
        query = query.filter(
            (Vehicle.registration_number.ilike(f'%{search}%')) |
            (Vehicle.make_model.ilike(f'%{search}%'))
        )
    if status:
        query = query.filter(Vehicle.operational_status == status)

    per_page = current_app.config.get('ITEMS_PER_PAGE', 10)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return render_template(
        'resources/vehicles.html',
        form=form,
        pagination=pagination,
        search=search,
        current_status=status
    )


@resources_bp.route('/vehicles/<int:id>/status', methods=['POST'])
@login_required
@role_required('Admin', 'SHO', 'Inspector')
def update_vehicle_status(id):
    vehicle = Vehicle.active().filter_by(id=id).first_or_404()
    new_status = request.form.get('operational_status')
    if new_status:
        try:
            vehicle.operational_status = new_status
            vehicle.updated_by = current_user.id
            db.session.commit()
            log_audit('UPDATE', 'vehicles', vehicle.id, description=f"Updated status of vehicle {vehicle.registration_number} to {new_status}")
            flash('Vehicle status updated.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating vehicle status: {str(e)}", 'danger')
    return redirect(url_for('resources.vehicles'))


@resources_bp.route('/vehicles/<int:id>/delete', methods=['POST'])
@login_required
@role_required('Admin', 'SHO')
def delete_vehicle(id):
    vehicle = Vehicle.active().filter_by(id=id).first_or_404()
    try:
        reg = vehicle.registration_number
        vehicle.soft_delete(current_user.id)
        db.session.commit()
        log_audit('SOFT_DELETE', 'vehicles', vehicle.id, description=f"Soft deleted vehicle {reg}")
        flash(f"Vehicle {reg} soft deleted successfully.", 'warning')
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting vehicle: {str(e)}", 'danger')
    return redirect(url_for('resources.vehicles'))


# ==================== WEAPONS ====================

@resources_bp.route('/weapons', methods=['GET', 'POST'])
@login_required
def weapons():
    form = WeaponForm()
    stations = PoliceStation.active().order_by(PoliceStation.name).all()
    form.station_id.choices = [(s.id, s.name) for s in stations]

    if form.validate_on_submit() and current_user.has_role('Admin', 'SHO'):
        try:
            existing = Weapon.active().filter_by(serial_number=form.serial_number.data).first()
            if existing:
                flash(f"Weapon with serial {form.serial_number.data} is already in armory.", 'danger')
            else:
                weapon = Weapon(
                    station_id=form.station_id.data,
                    serial_number=form.serial_number.data,
                    weapon_type=form.weapon_type.data,
                    caliber=form.caliber.data,
                    condition=form.condition.data,
                    storage_rack_number=form.storage_rack_number.data,
                    ammunition_capacity=form.ammunition_capacity.data,
                    created_by=current_user.id
                )
                db.session.add(weapon)
                db.session.commit()
                log_audit('CREATE', 'weapons', weapon.id, description=f"Added weapon {weapon.serial_number} to armory")
                flash(f"Weapon {weapon.serial_number} added to armory successfully.", 'success')
                return redirect(url_for('resources.weapons'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error cataloging weapon: {str(e)}", 'danger')

    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str).strip()
    query = Weapon.active().order_by(Weapon.id.desc())
    if search:
        query = query.filter(
            (Weapon.serial_number.ilike(f'%{search}%')) |
            (Weapon.weapon_type.ilike(f'%{search}%')) |
            (Weapon.storage_rack_number.ilike(f'%{search}%'))
        )
    per_page = current_app.config.get('ITEMS_PER_PAGE', 10)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return render_template('resources/weapons.html', form=form, pagination=pagination, search=search)


@resources_bp.route('/weapons/<int:id>/delete', methods=['POST'])
@login_required
@role_required('Admin', 'SHO')
def delete_weapon(id):
    weapon = Weapon.active().filter_by(id=id).first_or_404()
    try:
        sn = weapon.serial_number
        weapon.soft_delete(current_user.id)
        db.session.commit()
        log_audit('SOFT_DELETE', 'weapons', weapon.id, description=f"Soft deleted weapon {sn}")
        flash(f"Weapon {sn} decommissioned / soft deleted successfully.", 'warning')
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting weapon: {str(e)}", 'danger')
    return redirect(url_for('resources.weapons'))


# ==================== INVENTORY ====================

@resources_bp.route('/inventory', methods=['GET', 'POST'])
@login_required
def inventory():
    if request.method == 'POST' and current_user.has_role('Admin', 'SHO', 'Inspector'):
        try:
            item_name = request.form.get('item_name')
            category = request.form.get('item_category')
            station_id = request.form.get('station_id', type=int)
            total_qty = request.form.get('total_quantity', type=int, default=1)
            location = request.form.get('storage_location', 'Supply Room')
            uom = request.form.get('unit_of_measure', 'units')

            item = InventoryItem(
                station_id=station_id,
                item_category=category,
                item_name=item_name,
                total_quantity=total_qty,
                available_quantity=total_qty,
                unit_of_measure=uom,
                storage_location=location,
                created_by=current_user.id
            )
            db.session.add(item)
            db.session.commit()
            log_audit('CREATE', 'inventory_items', item.id, description=f"Added inventory item {item.item_name}")
            flash('Inventory item added successfully.', 'success')
            return redirect(url_for('resources.inventory'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error adding inventory: {str(e)}", 'danger')

    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str).strip()
    category = request.args.get('category', '', type=str).strip()

    query = InventoryItem.active().order_by(InventoryItem.item_name)
    if search:
        query = query.filter(InventoryItem.item_name.ilike(f'%{search}%'))
    if category:
        query = query.filter(InventoryItem.item_category == category)

    per_page = current_app.config.get('ITEMS_PER_PAGE', 10)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    stations = PoliceStation.active().order_by(PoliceStation.name).all()
    categories = ['Tactical Gear', 'Radios & Comms', 'Body Armor', 'First Aid / Medical', 'Forensics Kits', 'Office Supplies']

    return render_template(
        'resources/inventory.html',
        pagination=pagination,
        search=search,
        current_category=category,
        stations=stations,
        categories=categories
    )


@resources_bp.route('/inventory/<int:id>/delete', methods=['POST'])
@login_required
@role_required('Admin', 'SHO')
def delete_inventory(id):
    item = InventoryItem.active().filter_by(id=id).first_or_404()
    try:
        name = item.item_name
        item.soft_delete(current_user.id)
        db.session.commit()
        log_audit('SOFT_DELETE', 'inventory_items', item.id, description=f"Soft deleted inventory item {name}")
        flash(f"Item {name} soft deleted.", 'warning')
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting item: {str(e)}", 'danger')
    return redirect(url_for('resources.inventory'))
