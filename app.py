from flask import Flask, render_template, request, jsonify

# app.py
from src.pde_calculator import calculate_pde


app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/calculate_pde', methods=['POST'])

def calculate_pde_route():
    try:
        data = request.get_json()
        substance_name = data.get('substanceName', '').lower()
        result = calculate_pde(substance_name)
        return jsonify(result)
    except Exception as e:  
        print(f"Error: {e}")  # Log the error
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
