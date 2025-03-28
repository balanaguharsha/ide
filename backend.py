# Import necessary libraries
from flask import Flask, request, jsonify
import uuid # To generate unique IDs if items don't have them
from flask_cors import CORS # Import the CORS library

# Initialize the Flask application
app = Flask(__name__)

# --- Enable CORS ---
# This configuration allows requests from ALL origins.
CORS(app)


# --- Data Storage (In-Memory) ---
# (Same as before)
items = []
item_map = {}
swipes = {}
matches = []

# --- Helper Functions ---
# (Same as before)
def find_item_by_id(item_id):
  """Finds an item in the item_map by its ID."""
  return item_map.get(item_id)

def check_for_match(item_id, user1_id="user1", user2_id="user2"):
  """Checks if both specified users swiped right on the given item."""
  if item_id in swipes:
    item_swipes = swipes[item_id]
    if (user1_id in item_swipes and item_swipes[user1_id] == 'right' and
        user2_id in item_swipes and item_swipes[user2_id] == 'right'):
      if item_id not in matches:
        matches.append(item_id)
      return True
  return False

# --- API Endpoints ---
# (All endpoints remain the same as before)

@app.route('/')
def home():
  """Basic home route to confirm the server is running."""
  return "Swipe-to-match backend is running!"

@app.route('/load_items', methods=['POST'])
def load_items():
  """
  Loads a list of items into the backend.
  Expects JSON data: {'items': [{'id': 'unique_id', 'title': 'Item Title', ...}, ...]}
  """
  global items, item_map
  try:
    data = request.get_json()
    if not data or 'items' not in data or not isinstance(data['items'], list):
      return jsonify({"error": "Invalid input. Expected {'items': [list of item objects]}"}), 400

    new_items = data['items']
    items = []
    item_map = {}
    swipes.clear()
    matches.clear()

    for item in new_items:
        if not isinstance(item, dict):
            continue

        if 'id' not in item or not item['id']:
            item['id'] = str(uuid.uuid4())

        if item['id'] in item_map:
           print(f"Warning: Duplicate item ID '{item['id']}' found. Skipping.")
           continue

        items.append(item)
        item_map[item['id']] = item

    return jsonify({"message": f"{len(items)} items loaded successfully.", "total_items": len(items)}), 201
  except Exception as e:
    return jsonify({"error": f"An error occurred: {str(e)}"}), 500


@app.route('/items', methods=['GET'])
def get_items():
  """Returns the current list of items."""
  return jsonify({"items": items}), 200

@app.route('/swipe', methods=['POST'])
def handle_swipe():
  """
  Records a swipe for a user on an item and checks for matches.
  Expects JSON data: {'user_id': 'user1', 'item_id': 'm1', 'direction': 'right'}
  """
  try:
    data = request.get_json()
    if not data or not all(k in data for k in ('user_id', 'item_id', 'direction')):
      return jsonify({"error": "Missing required fields: user_id, item_id, direction"}), 400

    user_id = data['user_id']
    item_id = data['item_id']
    direction = data['direction'].lower()

    if user_id not in ["user1", "user2"]:
        return jsonify({"error": "Invalid user_id. Only 'user1' and 'user2' are supported in this example."}), 400
    if direction not in ['left', 'right']:
      return jsonify({"error": "Invalid direction. Must be 'left' or 'right'."}), 400
    if not find_item_by_id(item_id):
      return jsonify({"error": f"Item with ID '{item_id}' not found."}), 404

    if item_id not in swipes:
      swipes[item_id] = {}
    swipes[item_id][user_id] = direction

    print(f"Swipe recorded: User '{user_id}' swiped '{direction}' on item '{item_id}'")
    print(f"Current swipes for item '{item_id}': {swipes.get(item_id)}")

    match_found = False
    if direction == 'right':
      match_found = check_for_match(item_id)

    print(f"Match check result for item '{item_id}': {match_found}")
    print(f"Current matches: {matches}")

    response = {
        "message": "Swipe recorded successfully.",
        "match_status": "Match found!" if match_found else "No match yet."
    }
    return jsonify(response), 200

  except Exception as e:
    print(f"Error in /swipe: {str(e)}")
    return jsonify({"error": f"An server error occurred: {str(e)}"}), 500


@app.route('/matches', methods=['GET'])
def get_matches():
  """Returns the list of item IDs where both users matched."""
  matched_item_details = [find_item_by_id(item_id) for item_id in matches if find_item_by_id(item_id)]
  return jsonify({"matched_item_ids": matches, "matched_items": matched_item_details}), 200


# --- Run the App ---
if __name__ == '__main__':
  # debug=True should be False in production
  app.run(debug=False, port=5000) # Changed debug to False for typical deployment
