# Import necessary libraries
from flask import Flask, request, jsonify
import uuid
from flask_cors import CORS

# Initialize the Flask application
app = Flask(__name__)
CORS(app) # Allow all origins

# --- Data Storage (In-Memory) ---
items = []
item_map = {}
swipes = {} # Structure: swipes[item_id] = {'Amitha': 'direction', 'Harsha': 'direction'}
matches = [] # List of item_ids where both matched

# --- Helper Functions ---
def find_item_by_id(item_id):
  return item_map.get(item_id)

def check_for_match(item_id):
    expected_users = ["Amitha", "Harsha"]
    if item_id in swipes:
        item_swipes = swipes[item_id]
        if all(user in item_swipes for user in expected_users):
            if all(item_swipes[user] == 'right' for user in expected_users):
                if item_id not in matches:
                    matches.append(item_id)
                    print(f"New match found on item {item_id}!")
                return True
    return False

# --- API Endpoints ---

@app.route('/')
def home(): return "Swipe-to-match backend is running!"

@app.route('/load_items', methods=['POST'])
def load_items():
  global items, item_map, swipes, matches
  try:
    data = request.get_json(); # ... (validation) ...
    if not data or 'items' not in data or not isinstance(data['items'], list): return jsonify({"error": "Invalid input."}), 400
    new_items_data = data['items']; temp_items = []; temp_item_map = {}
    for item_data in new_items_data: # ... (process each item) ...
        item_id = item_data.get('id') or str(uuid.uuid4()); item_title = item_data.get('title', 'Untitled Item');
        if item_id in temp_item_map: continue
        new_item = {'id': item_id, 'title': item_title}; new_item.update({k: v for k, v in item_data.items() if k not in ['id', 'title']})
        temp_items.append(new_item); temp_item_map[item_id] = new_item
    items = temp_items; item_map = temp_item_map; swipes = {}; matches = [] # Reset all on load
    print(f"{len(items)} items loaded successfully."); return jsonify({"message": f"{len(items)} items loaded successfully.", "total_items": len(items)}), 201
  except Exception as e: print(f"Error in /load_items: {str(e)}"); return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@app.route('/add_item', methods=['POST'])
def add_item():
  global items, item_map
  try:
    data = request.get_json(); # ... (validation) ...
    if not data or 'title' not in data or not data['title'].strip(): return jsonify({"error": "Missing 'title' or title is empty."}), 400
    new_title = data['title'].strip(); new_item = { 'id': str(uuid.uuid4()), 'title': new_title }; new_item.update({k: v for k, v in data.items() if k not in ['id', 'title']})
    items.append(new_item); item_map[new_item['id']] = new_item
    print(f"Item added: {new_item}"); return jsonify({"message": "Item added successfully.", "item": new_item}), 201
  except Exception as e: print(f"Error in /add_item: {str(e)}"); return jsonify({"error": f"An server error occurred: {str(e)}"}), 500

@app.route('/items', methods=['GET'])
def get_items(): return jsonify({"items": list(items)}), 200

@app.route('/items', methods=['DELETE'])
def clear_all_items():
  global items, item_map, swipes, matches
  try:
    item_count = len(items); items = []; item_map = {}; swipes = {}; matches = []
    print(f"Cleared all data. {item_count} items removed."); return jsonify({"message": f"All data cleared successfully. {item_count} items were removed."}), 200
  except Exception as e: print(f"Error in /items DELETE: {str(e)}"); return jsonify({"error": f"An server error occurred: {str(e)}"}), 500

@app.route('/swipe', methods=['POST'])
def handle_swipe():
  global swipes
  try:
    data = request.get_json() # ... (validation) ...
    if not data or not all(k in data for k in ('user_id', 'item_id', 'direction')): return jsonify({"error": "Missing fields"}), 400
    user_id = data['user_id']; item_id = data['item_id']; direction = data['direction'].lower()
    if user_id not in ["Amitha", "Harsha"]: return jsonify({"error": "Invalid user_id."}), 400
    if direction not in ['left', 'right']: return jsonify({"error": "Invalid direction."}), 400
    if not find_item_by_id(item_id): return jsonify({"error": f"Item '{item_id}' not found."}), 404

    if item_id not in swipes: swipes[item_id] = {}
    swipes[item_id][user_id] = direction
    print(f"Swipe: User '{user_id}' swiped '{direction}' on item '{item_id}'")

    match_found = False
    if direction == 'right': match_found = check_for_match(item_id)
    print(f"Match check: {match_found}")

    response = { "message": "Swipe recorded.", "match_status": "Match found!" if match_found else "No match yet." }
    return jsonify(response), 200
  except Exception as e: print(f"Error in /swipe: {str(e)}"); return jsonify({"error": f"An server error occurred: {str(e)}"}), 500

@app.route('/matches', methods=['GET'])
def get_matches():
  matched_item_details = [find_item_by_id(item_id) for item_id in matches if find_item_by_id(item_id)]
  return jsonify({"matched_item_ids": matches, "matched_items": matched_item_details}), 200

@app.route('/swipes/<user_id>', methods=['GET'])
def get_user_swipes(user_id):
    if user_id not in ["Amitha", "Harsha"]: return jsonify({"error": "Invalid user_id specified."}), 400
    user_swipe_history = {}
    for item_id, item_swipes_dict in swipes.items():
        if user_id in item_swipes_dict: user_swipe_history[item_id] = item_swipes_dict[user_id]
    print(f"Returning swipe history for {user_id}: {len(user_swipe_history)} items")
    return jsonify({"swiped_items": user_swipe_history}), 200

# --- Updated DELETE /swipes/<user_id> ---
@app.route('/swipes/<user_id>', methods=['DELETE'])
def delete_user_swipes(user_id):
    """Deletes all swipe records for the specified user AND clears all matches."""
    global swipes, matches # Ensure we can modify both
    if user_id not in ["Amitha", "Harsha"]:
        return jsonify({"error": "Invalid user_id specified."}), 400

    cleared_count = 0
    item_ids_to_check = list(swipes.keys())
    for item_id in item_ids_to_check:
        if item_id in swipes and user_id in swipes[item_id]:
            del swipes[item_id][user_id]
            cleared_count += 1
            # Optional: Remove item entry if no swipes left?
            # if not swipes[item_id]: del swipes[item_id]

    # --- ADDED: Clear the global matches list ---
    matches_cleared_count = len(matches)
    matches = []
    print(f"Cleared {cleared_count} swipe records for user {user_id}. Also cleared {matches_cleared_count} matches.")
    # --- END ADDED ---

    return jsonify({"message": f"Cleared {cleared_count} swipe records for user {user_id}. All matches cleared."}), 200
# --- END Updated DELETE /swipes/<user_id> ---

# --- Run the App ---
if __name__ == '__main__':
  app.run(debug=False)
