from flask import Blueprint, jsonify

parent_bp = Blueprint('parent', __name__)

@parent_bp.route('', methods=['GET'])
def get_parent():
    return jsonify({"message": "Parent module placeholder"})
