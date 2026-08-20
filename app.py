from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({"message": "Welcome to Farmrt"})
@app.route("/status")

def status():
    return jsonify(status="ok"),200


if __name__ == '__main__':
    app.run(debug=True)