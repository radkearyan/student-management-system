from flask import Blueprint, jsonify

timetable_bp = Blueprint('timetable', __name__)

@timetable_bp.route('', methods=['GET'])
def get_timetable():
    return jsonify({"message": "Timetable module placeholder"})
