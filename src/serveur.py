from flask import Flask, request, render_template
import os

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        text = request.form['text']
        if text:
            if not os.path.exists('../log'):
                os.makedirs('../log')
            with open('../log/saved_text.txt', 'w') as file:
                file.write(text)
            return "Text saved successfully."
    return render_template('index.html')
    
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=2937)