from datetime import date, datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app, jsonify
from extensions import db
from models import Trip, User, Itinerary
from routes.forms import TripForm
from utils.decorators import login_required
from services.ai import generate_itinerary_data, adapt_itinerary_for_weather
from services.weather import get_weather_forecast

trips_bp = Blueprint('trips', __name__)

# List of popular destinations with placeholders for design
POPULAR_DESTINATIONS = [
    {"name": "Goa", "desc": "Beaches, sunsets, and vibrant nightlife.", "image": "goa.jpg"},
    {"name": "Jaipur", "desc": "Explore the historic palaces and pink city architecture.", "image": "jaipur.jpg"},
    {"name": "Manali", "desc": "Snow-capped peaks and adventurous valley trails.", "image": "manali.jpg"},
    {"name": "Kerala", "desc": "Peaceful backwaters and lush tea plantations.", "image": "kerala.jpg"}
]

# List of interests for travelers to choose
AVAILABLE_INTERESTS = [
    "Adventure", "Food & Dining", "Historical", "Nature & Wildlife", 
    "Beaches", "Shopping", "Relaxation", "Art & Culture"
]

@trips_bp.route('/dashboard')
@login_required
def dashboard():
    user = User.query.get(session['user_id'])
    
    # Retrieve user's trips
    user_trips = Trip.query.filter_by(user_id=user.id).order_by(Trip.start_date.asc()).all()
    
    today = date.today()
    upcoming_trips = [t for t in user_trips if t.start_date >= today]
    recent_trips = [t for t in user_trips if t.start_date < today]
    
    # Quick statistics for the dashboard
    total_trips = len(user_trips)
    total_budget = sum([float(t.budget) for t in user_trips])
    
    return render_template(
        'dashboard.html', 
        user=user, 
        upcoming_trips=upcoming_trips, 
        recent_trips=recent_trips,
        total_trips=total_trips,
        total_budget=total_budget,
        popular_destinations=POPULAR_DESTINATIONS
    )

@trips_bp.route('/trips/create', methods=['GET', 'POST'])
@login_required
def create():
    form = TripForm()
    
    # Pre-populate destination if passed in URL query
    if request.method == 'GET' and request.args.get('dest'):
        form.destination.data = request.args.get('dest')
        
    if form.validate_on_submit():
        # Retrieve interests from request form
        selected_interests = request.form.getlist('interests')
        
        trip = Trip(
            user_id=session['user_id'],
            destination=form.destination.data.strip(),
            budget=form.budget.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            travellers=form.travellers.data,
            interests=selected_interests,
            status='planned'
        )
        
        try:
            db.session.add(trip)
            db.session.commit()
            flash('Trip planned successfully!', 'success')
            return redirect(url_for('trips.dashboard'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while saving the trip. Please try again.', 'danger')
            current_app.logger.error(f"Trip Creation Error: {str(e)}")
            
    return render_template('trips/create.html', form=form, available_interests=AVAILABLE_INTERESTS)

@trips_bp.route('/trips/<int:trip_id>')
@login_required
def view(trip_id):
    trip = Trip.query.filter_by(id=trip_id, user_id=session['user_id']).first_or_404()
    
    # Retrieve specific version if requested in URL (e.g. ?version=2), else get the latest version
    version_req = request.args.get('version', type=int)
    if version_req:
        itinerary = Itinerary.query.filter_by(trip_id=trip.id, version=version_req).first()
    else:
        itinerary = Itinerary.query.filter_by(trip_id=trip.id).order_by(Itinerary.version.desc()).first()
        
    # Get a list of all available versions to show toggles in view page
    all_versions = db.session.query(Itinerary.version).filter_by(trip_id=trip.id).order_by(Itinerary.version.asc()).all()
    version_list = [v[0] for v in all_versions]
    
    # Fetch weather forecast
    forecast = get_weather_forecast(trip.destination)
        
    return render_template(
        'trips/view.html', 
        trip=trip, 
        itinerary=itinerary, 
        version_list=version_list,
        current_version=itinerary.version if itinerary else None,
        forecast=forecast
    )

@trips_bp.route('/trips/<int:trip_id>/generate-itinerary', methods=['POST'])
@login_required
def generate_itinerary(trip_id):
    trip = Trip.query.filter_by(id=trip_id, user_id=session['user_id']).first_or_404()
    
    trip_data = {
        'destination': trip.destination,
        'budget': float(trip.budget),
        'start_date': trip.start_date,
        'end_date': trip.end_date,
        'travellers': trip.travellers,
        'interests': trip.interests
    }
    
    try:
        # Call OpenRouter to generate data
        itinerary_json = generate_itinerary_data(trip_data)
        
        # Calculate version number
        latest_itinerary = Itinerary.query.filter_by(trip_id=trip.id).order_by(Itinerary.version.desc()).first()
        next_version = (latest_itinerary.version + 1) if latest_itinerary else 1
        
        # Save itinerary
        itinerary = Itinerary(
            trip_id=trip.id,
            ai_itinerary=itinerary_json,
            version=next_version
        )
        
        db.session.add(itinerary)
        db.session.commit()
        
        flash(f"Itinerary version v{next_version} generated successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Failed to generate itinerary: {str(e)}", "danger")
        current_app.logger.error(f"Itinerary Generation Exception: {str(e)}")
        
    return redirect(url_for('trips.view', trip_id=trip.id))

@trips_bp.route('/trips/<int:trip_id>/adapt-weather', methods=['POST'])
@login_required
def adapt_weather(trip_id):
    trip = Trip.query.filter_by(id=trip_id, user_id=session['user_id']).first_or_404()
    
    # Retrieve the latest generated itinerary
    itinerary = Itinerary.query.filter_by(trip_id=trip.id).order_by(Itinerary.version.desc()).first()
    if not itinerary:
        flash("Please generate an itinerary first before adapting to weather.", "warning")
        return redirect(url_for('trips.view', trip_id=trip.id))
        
    # Retrieve weather forecast
    forecast = get_weather_forecast(trip.destination)
    if not forecast:
        flash("Failed to fetch weather forecast. Please ensure your OpenWeather API key is correct.", "danger")
        return redirect(url_for('trips.view', trip_id=trip.id))
        
    trip_data = {
        'destination': trip.destination,
        'budget': float(trip.budget),
        'start_date': trip.start_date,
        'end_date': trip.end_date,
        'travellers': trip.travellers,
        'interests': trip.interests
    }
    
    try:
        # Call AI adaptation service
        adapted_json = adapt_itinerary_for_weather(trip_data, itinerary.ai_itinerary, forecast)
        
        # Calculate next version
        next_version = itinerary.version + 1
        new_itinerary = Itinerary(
            trip_id=trip.id,
            ai_itinerary=adapted_json,
            version=next_version
        )
        
        db.session.add(new_itinerary)
        db.session.commit()
        
        flash(f"Itinerary adapted to weather successfully! Saved as version v{next_version}.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Failed to adapt itinerary to weather: {str(e)}", "danger")
        current_app.logger.error(f"Weather Adaptation Exception: {str(e)}")
        
    return redirect(url_for('trips.view', trip_id=trip.id))

@trips_bp.route('/trips/<int:trip_id>/itinerary/history')
@login_required
def itinerary_history(trip_id):
    trip = Trip.query.filter_by(id=trip_id, user_id=session['user_id']).first_or_404()
    itineraries = Itinerary.query.filter_by(trip_id=trip.id).order_by(Itinerary.version.desc()).all()
    return render_template('trips/itinerary_history.html', trip=trip, itineraries=itineraries)

@trips_bp.route('/trips/<int:trip_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(trip_id):
    trip = Trip.query.filter_by(id=trip_id, user_id=session['user_id']).first_or_404()
    form = TripForm(obj=trip)
    
    if form.validate_on_submit():
        # Retrieve updated interests
        selected_interests = request.form.getlist('interests')
        
        trip.destination = form.destination.data.strip()
        trip.budget = form.budget.data
        trip.start_date = form.start_date.data
        trip.end_date = form.end_date.data
        trip.travellers = form.travellers.data
        trip.interests = selected_interests
        
        # Automatically update status if dates changed
        today = date.today()
        if trip.start_date < today:
            trip.status = 'completed'
        else:
            trip.status = 'planned'
            
        try:
            db.session.commit()
            flash('Trip details updated successfully!', 'success')
            return redirect(url_for('trips.view', trip_id=trip.id))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating the trip.', 'danger')
            current_app.logger.error(f"Trip Update Error: {str(e)}")
            
    return render_template('trips/edit.html', form=form, trip=trip, available_interests=AVAILABLE_INTERESTS)

@trips_bp.route('/trips/<int:trip_id>/delete', methods=['POST'])
@login_required
def delete(trip_id):
    trip = Trip.query.filter_by(id=trip_id, user_id=session['user_id']).first_or_404()
    try:
        db.session.delete(trip)
        db.session.commit()
        flash('Trip has been deleted.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while deleting the trip.', 'danger')
        current_app.logger.error(f"Trip Delete Error: {str(e)}")
        
    return redirect(url_for('trips.dashboard'))

@trips_bp.route('/api/trips/<int:trip_id>/map-data', methods=['GET'])
@login_required
def get_trip_map_data(trip_id):
    trip = Trip.query.filter_by(id=trip_id, user_id=session['user_id']).first_or_404()
    
    from services.maps import get_destination_map_data
    try:
        map_data = get_destination_map_data(trip.destination)
        return jsonify({
            "success": True,
            "destination": trip.destination,
            "lat": map_data["lat"],
            "lon": map_data["lon"],
            "pois": map_data["pois"]
        })
    except Exception as e:
        current_app.logger.error(f"Error fetching map data: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500
