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
items = []
item_map = {} # Dictionary for quick lookup by ID: {item_id: item_data}
swipes = {}
matches = []

# --- Helper Functions ---
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

@app.route('/')
def home():
  """Basic home route to confirm the server is running."""
  return "Swipe-to-match backend is running!"

@app.route('/load_items', methods=['POST'])
def load_items():
  """
  Loads/Replaces the list of items in the backend.
  Expects JSON data: {'items': [{'id': 'unique_id', 'title': 'Item Title', ...}, ...]}
  """
  global items, item_map, swipes, matches # Ensure swipes/matches are cleared too
  try:
    data = request.get_json()
    if not data or 'items' not in data or not isinstance(data['items'], list):
      return jsonify({"error": "Invalid input. Expected {'items': [list of item objects]}"}), 400

    new_items_data = data['items']
    temp_items = []
    temp_item_map = {}

    for item_data in new_items_data:
        if not isinstance(item_data, dict):
            print(f"Warning: Invalid item format skipped: {item_data}")
            continue # Skip invalid item formats

        # Ensure each item has a unique ID
        item_id = item_data.get('id') or str(uuid.uuid4()) # Use provided or generate new
        item_title = item_data.get('title', 'Untitled Item') # Default title if missing

        if item_id in temp_item_map:
           print(f"Warning: Duplicate item ID '{item_id}' found during load. Skipping.")
           continue # Avoid duplicates within the load itself

        new_item = {'id': item_id, 'title': item_title}
        # Add any other fields from item_data if needed
        new_item.update({k: v for k, v in item_data.items() if k not in ['id', 'title']})

        temp_items.append(new_item)
        temp_item_map[item_id] = new_item

    # Replace existing data only after successful processing
    items = temp_items
    item_map = temp_item_map
    swipes = {} # Clear previous swipes when loading new items
    matches = [] # Clear previous matches

    print(f"{len(items)} items loaded successfully.")
    return jsonify({"message": f"{len(items)} items loaded successfully.", "total_items": len(items)}), 201

  except Exception as e:
    print(f"Error in /load_items: {str(e)}")
    return jsonify({"error": f"An error occurred: {str(e)}"}), 500

# --- NEW ENDPOINT ---
@app.route('/add_item', methods=['POST'])
def add_item():
    """Adds a single new item to the list."""
    global items, item_map
    try:
        data = request.get_json()
        # Ensure title exists and is not just whitespace
        if not data or 'title' not in data or not data['title'].strip():
            return jsonify({"error": "Missing 'title' or title is empty."}), 400

        new_title = data['title'].strip()

        # Optional: Check if an item with the same title already exists
        # if any(item['title'].lower() == new_title.lower() for item in items):
        #     return jsonify({"error": f"Item with title '{new_title}' already exists."}), 409 # 409 Conflict

        new_item = {
            'id': str(uuid.uuid4()), # Generate unique ID
            'title': new_title
            # Add other potential fields from data if needed
        }
        new_item.update({k: v for k, v in data.items() if k not in ['id', 'title']})


        items.append(new_item)
        item_map[new_item['id']] = new_item

        print(f"Item added: {new_item}")
        # Return the newly created item along with success message
        return jsonify({"message": "Item added successfully.", "item": new_item}), 201

    except Exception as e:
        print(f"Error in /add_item: {str(e)}")
        return jsonify({"error": f"An server error occurred: {str(e)}"}), 500
# --- END NEW ENDPOINT ---

@app.route('/items', methods=['GET'])
def get_items():
  """Returns the current list of items."""
  # Return a copy to avoid potential modification issues if needed elsewhere
  return jsonify({"items": list(items)}), 200

@app.route('/swipe', methods=['POST'])
def handle_swipe():
  """
  Records a swipe for a user on an item and checks for matches.
  Expects JSON data: {'user_id': 'user1', 'item_id': 'm1', 'direction': 'right'}
  """
  global swipes # Ensure we're modifying the global swipes dict
  try:
    data = request.get_json()
    if not data or not all(k in data for k in ('user_id', 'item_id', 'direction')):
      return jsonify({"error": "Missing required fields: user_id, item_id, direction"}), 400

    user_id = data['user_id']
    item_id = data['item_id']
    direction = data['direction'].lower()

    # Validate user ID
    if user_id not in ["user1", "user2"]:
        return jsonify({"error": "Invalid user_id. Only 'user1' and 'user2' are supported in this example."}), 400
    # Validate direction
    if direction not in ['left', 'right']:
      return jsonify({"error": "Invalid direction. Must be 'left' or 'right'."}), 400
    # Validate item ID exists
    if not find_item_by_id(item_id):
      # Maybe the item was deleted? Or ID is wrong.
      return jsonify({"error": f"Item with ID '{item_id}' not found."}), 404

    # Record the swipe
    if item_id not in swipes:
      swipes[item_id] = {}
    swipes[item_id][user_id] = direction

    print(f"Swipe recorded: User '{user_id}' swiped '{direction}' on item '{item_id}'")
    print(f"Current swipes for item '{item_id}': {swipes.get(item_id)}") # Debugging

    # Check for a match if the swipe was 'right'
    match_found = False
    if direction == 'right':
      match_found = check_for_match(item_id) # Uses default user IDs 'user1', 'user2'

    print(f"Match check result for item '{item_id}': {match_found}") # Debugging
    print(f"Current matches: {matches}") # Debugging

    response = {
        "message": "Swipe recorded successfully.",
        "match_status": "Match found!" if match_found else "No match yet."
    }
    return jsonify(response), 200

  except Exception as e:
    print(f"Error in /swipe: {str(e)}") # Log the error server-side
    return jsonify({"error": f"An server error occurred: {str(e)}"}), 500


@app.route('/matches', methods=['GET'])
def get_matches():
  """Returns the list of item details where both users matched."""
  # Use the helper function to ensure we get full item details
  matched_item_details = [find_item_by_id(item_id) for item_id in matches if find_item_by_id(item_id)]
  # Return both IDs and full details for flexibility
  return jsonify({"matched_item_ids": matches, "matched_items": matched_item_details}), 200


# --- Run the App ---
if __name__ == '__main__':
  # Set debug=False for production/deployment
  # The port is often handled by the deployment platform (like Render),
  # but can be specified for local testing. Render uses PORT env var.
  app.run(debug=False)
