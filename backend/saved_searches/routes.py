from backend.db.db_connection import session
from backend.saved_searches import saved_search_bp
from sqlalchemy import select, delete
from backend.db.models import SavedSearch
from flask import jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from datetime import date, timedelta

@saved_search_bp.route("/", methods=["GET"])
@jwt_required()
def get_all_saved_searches():
    user_id = int(get_jwt_identity())
    saved_searches = session.execute(select(SavedSearch).where(SavedSearch.user_id==user_id).order_by(SavedSearch.recorded_at.desc())).scalars().all()
    results = []
    for search in saved_searches:
        results.append({
            "id": str(search.id),  
            "destination": search.destination,
            "checkIn": search.check_in.isoformat(),
            "checkOut": search.check_out.isoformat(),
            "guests": search.guests,
            "filters": search.filters or {},
            "sorting": search.sorting or {},
            "savedAt": search.recorded_at.isoformat() if search.recorded_at else None
        })
    return jsonify({"results": results}), 200

@saved_search_bp.route("/", methods=["POST"])
@jwt_required()
def create_saved_search():
    user_id = int(get_jwt_identity())
    data = request.get_json()
        
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400
    
    destination = data.get("destination")
    check_in_str = data.get("check_in")
    check_out_str = data.get("check_out")
    guests = data.get("guests")

    try:
        check_in = date.fromisoformat(check_in_str)
        check_out = date.fromisoformat(check_out_str)
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
    
    filters = {
        "max_price": data.get("max_price"),
        "min_rating": data.get("min_rating"), 
        "amenities": data.get("amenities", [])
    }

    sorting = {
        "sort_field": data.get("sort_field"),
        "sort_order": data.get("sort_order")
    }
    new_search = SavedSearch(user_id=user_id, destination=destination, check_in=check_in, check_out=check_out, guests=guests, filters=filters, sorting=sorting)
    session.add(new_search)
    session.commit()
    return jsonify({
        "message": "Saved search created successfully",
        "id": new_search.id
    }), 201

@saved_search_bp.route("/<int:saved_search_id>", methods=["DELETE"])
@jwt_required()
def delete_saved_search(saved_search_id):
    session.execute(delete(SavedSearch).where(SavedSearch.id==saved_search_id))
    session.commit()
    return jsonify({"message": "Saved search deleted successfully"}), 200
