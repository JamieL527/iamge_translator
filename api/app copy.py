from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

print("Flask app created")

@app.route('/')
def root():
    print("Root route accessed")
    return "Flask server is running!"

@app.route('/api/hello')
def hello_world():
    print("Hello route accessed")
    return jsonify({"message": "Hello, World!"})

if __name__ == '__main__':
    print("Starting Flask application...")
    app.run(debug=True, port=5001)  # Change port to 5001
else:
    print("App imported, __name__ is:", __name__)