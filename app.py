from flask import Flask, render_template, request, jsonify
import re
from collections import Counter
from flask_cors import CORS, cross_origin


app = Flask(__name__)
CORS(app, allow_headers="*", origins="*")


from data import input_text

def process_text(text):
    # Remove page numbering (e.g., "3of 18" or "4 of 16") and lines containing "filename"
    text = re.sub(r'\b\d+\s*of\s*\d+\b', '', text)
    text = re.sub(r'filename', '', text, flags=re.IGNORECASE)

    # Split the text into separate machines
    machines = []
    current_machine = ""
    for line in text.split('\n'):
        if line.startswith("27465"):
            if current_machine:
                machines.append(current_machine)
                current_machine = ""
        current_machine += line + "\n"
    
    # Add the last machine if there is any
    if current_machine:
        machines.append(current_machine)

    return machines

def extract_configuration_lines(machines, keyword):
    configurations = []
    keyword_lines_count = 0
    for machine in machines:
        machine_lines = machine.strip().split('\n')
        collecting = False
        for line in machine_lines:
            if line.startswith("27465") and keyword.lower() in line.lower():
                collecting = True
                keyword_lines_count += 1
                continue
            if collecting:
                if line.startswith("27465"):  # Next machine starts
                    break
                # Adjust the regular expression to match the format of dimension values
                # Example: r'\b\d+\s?mm\b' matches '100mm' or '100 mm'
                line_with_placeholder = re.sub(r'\b\d+\s?mm\b', '[...]', line)
                configurations.append(line_with_placeholder)

    # Count the frequency of each line
    line_counts = Counter(configurations)
    common_lines = line_counts.most_common()
    return common_lines, keyword_lines_count

def get_configuration_items_for_keyword(keyword):
    machines = process_text(input_text)
    common_lines, _ = extract_configuration_lines(machines, keyword)
    return [line for line, _ in common_lines]  # Return just the lines, not the counts





@cross_origin(origin='*', headers=['Content-Type'])
@app.route('/fetch_configuration_items', methods=['POST'])
def fetch_configuration_items():
    data = request.get_json()
    keyword = data.get('keyword')
    items = get_configuration_items_for_keyword(keyword)
    return jsonify({'items': items})

@app.route('/', methods=['GET', 'POST'])
def index():
    selected_keyword = 'conveyor'  # Default keyword
    machines = process_text(input_text)
    common_lines, keyword_lines_count = extract_configuration_lines(machines, selected_keyword)
    
    if request.method == 'POST':
        selected_keyword = request.form.get('keyword')
        common_lines, keyword_lines_count = extract_configuration_lines(machines, selected_keyword)

    return render_template('index.html', 
                           keywords=['conveyor', 'washer', 'tipper'], 
                           selected_keyword=selected_keyword, 
                           common_lines=common_lines, 
                           keyword_lines_count=keyword_lines_count)

if __name__ == '__main__':
    app.run(debug=True)