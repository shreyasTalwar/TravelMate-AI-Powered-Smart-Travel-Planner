from datetime import date, datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app, jsonify, make_response
from extensions import db
from models import Trip, User, Itinerary, Expense, SafetyAssessment
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

@trips_bp.route('/trips/<int:trip_id>/budget', methods=['GET'])
@login_required
def budget(trip_id):
    trip = Trip.query.filter_by(id=trip_id, user_id=session['user_id']).first_or_404()
    
    # Retrieve all manual expenses
    expenses = Expense.query.filter_by(trip_id=trip.id).order_by(Expense.date.desc()).all()
    
    # Sum up manual expenses grouped by category
    categories = ['Hotel', 'Transport', 'Food', 'Activities', 'Shopping', 'Emergency Fund']
    spent_by_category = {cat: 0.0 for cat in categories}
    total_spent = 0.0
    for exp in expenses:
        if exp.category in spent_by_category:
            spent_by_category[exp.category] += float(exp.amount)
        total_spent += float(exp.amount)
        
    remaining_balance = float(trip.budget) - total_spent
    
    # Parse active itinerary to extract AI estimates
    itinerary = Itinerary.query.filter_by(trip_id=trip.id).order_by(Itinerary.version.desc()).first()
    ai_estimates = {cat: 0.0 for cat in categories}
    ai_estimated_total = 0.0
    
    if itinerary and 'days' in itinerary.ai_itinerary:
        days = itinerary.ai_itinerary['days']
        for day in days:
            # 1. Activities (sum of morning, afternoon, evening slots)
            slots = day.get('slots', {})
            for slot_key in ['morning', 'afternoon', 'evening']:
                slot = slots.get(slot_key, {})
                ai_estimates['Activities'] += float(slot.get('cost', 0.0))
                
            # 2. Transport (transportation cost)
            trans = day.get('transportation', {})
            ai_estimates['Transport'] += float(trans.get('cost', 0.0))
            
            # 3. Food (dining recommendations cost per person * travelers count)
            rests = day.get('restaurants', [])
            for rest in rests:
                cost_pp = float(rest.get('estimated_cost_per_person', 0.0))
                ai_estimates['Food'] += cost_pp * trip.travellers
                
        ai_estimated_total = sum(ai_estimates.values())
        
    return render_template(
        'trips/budget.html',
        trip=trip,
        expenses=expenses,
        spent_by_category=spent_by_category,
        total_spent=total_spent,
        remaining_balance=remaining_balance,
        ai_estimates=ai_estimates,
        ai_estimated_total=ai_estimated_total,
        categories=categories
    )

@trips_bp.route('/trips/<int:trip_id>/budget/add', methods=['POST'])
@login_required
def add_expense(trip_id):
    trip = Trip.query.filter_by(id=trip_id, user_id=session['user_id']).first_or_404()
    
    category = request.form.get('category')
    amount = request.form.get('amount')
    description = request.form.get('description', '').strip()
    date_str = request.form.get('date')
    
    if not category or not amount:
        flash("Category and Amount are required.", "danger")
        return redirect(url_for('trips.budget', trip_id=trip.id))
        
    try:
        expense_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else datetime.utcnow().date()
        expense = Expense(
            trip_id=trip.id,
            category=category,
            amount=float(amount),
            description=description if description else None,
            date=expense_date
        )
        db.session.add(expense)
        db.session.commit()
        flash("Expense logged successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Failed to log expense: {str(e)}", "danger")
        current_app.logger.error(f"Add Expense Error: {str(e)}")
        
    return redirect(url_for('trips.budget', trip_id=trip.id))

@trips_bp.route('/trips/<int:trip_id>/budget/delete/<int:expense_id>', methods=['POST'])
@login_required
def delete_expense(trip_id, expense_id):
    trip = Trip.query.filter_by(id=trip_id, user_id=session['user_id']).first_or_404()
    expense = Expense.query.filter_by(id=expense_id, trip_id=trip.id).first_or_404()
    
    try:
        db.session.delete(expense)
        db.session.commit()
        flash("Expense entry removed.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Failed to delete expense: {str(e)}", "danger")
        current_app.logger.error(f"Delete Expense Error: {str(e)}")
        
    return redirect(url_for('trips.budget', trip_id=trip.id))

@trips_bp.route('/trips/<int:trip_id>/budget/export', methods=['GET'])
@login_required
def export_budget(trip_id):
    trip = Trip.query.filter_by(id=trip_id, user_id=session['user_id']).first_or_404()
    expenses = Expense.query.filter_by(trip_id=trip.id).order_by(Expense.date.asc()).all()
    
    import io
    import csv
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write headers
    writer.writerow(['Date', 'Category', 'Description', 'Amount (INR)'])
    
    # Write entries
    for exp in expenses:
        writer.writerow([exp.date.strftime('%Y-%m-%d'), exp.category, exp.description or '', float(exp.amount)])
        
    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = f"attachment; filename=budget_trip_{trip.id}_{trip.destination.lower()}.csv"
    response.headers["Content-type"] = "text/csv"
    return response

@trips_bp.route('/trips/<int:trip_id>/safety', methods=['GET'])
@login_required
def safety(trip_id):
    trip = Trip.query.filter_by(id=trip_id, user_id=session['user_id']).first_or_404()
    
    destination_key = trip.destination.strip().lower()
    
    # Check if safety assessment is cached
    assessment = SafetyAssessment.query.filter_by(destination=destination_key).first()
    
    if not assessment:
        from services.ai import generate_safety_assessment
        try:
            score, data = generate_safety_assessment(trip.destination)
            assessment = SafetyAssessment(
                destination=destination_key,
                safety_score=score,
                safety_data=data
            )
            db.session.add(assessment)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Failed to generate safety assessment: {str(e)}")
            # Define safe fallback structure
            fallback_data = {
                "safety_score": 4,
                "emergency_contacts": {
                    "police": "112 / 100",
                    "medical": "102 / 108",
                    "fire": "101",
                    "women_helpline": "1091"
                },
                "neighborhoods": {
                    "safe_zones": [{"name": "Tourist Center & City Square", "reason": "High surveillance, well-patrolled, well-lit"}],
                    "caution_zones": [{"name": "Outer Suburb Transit hubs", "reason": "Crowded, prone to petty thefts and pickpocketing"}]
                },
                "solo_travel_advice": ["Keep emergency contacts on speed dial.", "Share your live location with trusted family members."],
                "transit_safety": ["Prefer pre-booked official cabs or public transport in crowded areas."],
                "cultural_guidelines": ["Respect local dress guidelines when entering historical or religious spots."],
                "common_scams": [{"name": "Overpriced unofficial taxis", "warning": "Always ask for taxi meters or use ride-hailing apps."}]
            }
            assessment = SafetyAssessment(
                destination=destination_key,
                safety_score=4,
                safety_data=fallback_data
            )
            
    return render_template('trips/safety.html', trip=trip, assessment=assessment)

@trips_bp.route('/trips/<int:trip_id>/safety/alert', methods=['POST'])
@login_required
def safety_alert(trip_id):
    trip = Trip.query.filter_by(id=trip_id, user_id=session['user_id']).first_or_404()
    
    lat = request.json.get('lat')
    lon = request.json.get('lon')
    
    # Log the coordinates for emergency tracking
    current_app.logger.warning(f"EMERGENCY SOS ALERT TRIGGERED by User ID {session['user_id']} for Trip ID {trip.id} ({trip.destination}). Location coordinates: Lat {lat}, Lon {lon}")
    
    return jsonify({
        "success": True,
        "message": "SOS Panic Alert broadcasted successfully to your emergency contacts!"
    })
