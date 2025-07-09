from flask import Flask, request, jsonify
from pymongo import MongoClient
from datetime import datetime
import os

app = Flask(__name__)
client = MongoClient("mongodb://localhost:27017")
db = client["webhook_db"]
collection = db["github_events"]

@app.route('/')
def home():
    return "<h3>Webhook Receiver is Running</h3>"

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    print("Webhook received:", data)
    # return "OK", 200
    event = request.headers.get('X-GitHub-Event')

    if event == "push":
        author = data['pusher']['name']
        to_branch = data['ref'].split('/')[-1]
        collection.insert_one({
            "action": "push",
            "author": author,
            "to_branch": to_branch,
            "timestamp": datetime.utcnow()
        })

    elif event == "pull_request":
        pr = data['pull_request']
        author = pr['user']['login']
        from_branch = pr['head']['ref']
        to_branch = pr['base']['ref']
        is_merged = pr['merged']
        action = "merge" if is_merged else "pull_request"
        collection.insert_one({
            "action": action,
            "author": author,
            "from_branch": from_branch,
            "to_branch": to_branch,
            "timestamp": datetime.utcnow()
        })

    return jsonify({"status": "success"}), 200

@app.route('/events', methods=['GET'])
def get_events():
    events = list(collection.find().sort("timestamp", -1).limit(10))
    for e in events:
        e['_id'] = str(e['_id'])
    return jsonify(events)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
