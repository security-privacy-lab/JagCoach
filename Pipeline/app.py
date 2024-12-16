import os
from flask import Flask, flash, render_template, request, redirect, url_for, send_file, jsonify
from werkzeug.utils import secure_filename
import Pipeline2
import json

UPLOAD_FOLDER = "/home/rudito/Code/Cao_Research/JagCoach/Pipeline"
ALLOWED_EXTENSIONS = {"mp4", "webm"}

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
# This key may have to be something more secure later? It's for cookies and sessions.
app.config['SECRET_KEY'] = os.urandom(24)


@app.route("/")
def index():
    return render_template("upload.html")

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/download/<filename>")
def download_file(filename):
    return send_file(
        os.path.join(app.config["UPLOAD_FOLDER"], filename), as_attachment=True
    )


@app.route("/upload", methods=["POST"])
def upload_file():
    if request.method == "POST":
        # check if the post request has the file part
        if "file" not in request.files:
            flash("No file part")
            return jsonify({'error': 'No file part'}), 400
        file = request.files["file"]
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == "":
            flash("No selected file")
            return jsonify({'error': 'No selected file'}), 400
        if file and allowed_file(file.filename):
            # Save the uploaded file
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(file_path)

            # Return a JSON response with the filename
            return jsonify({'filename': filename}), 200

    # Render the upload form if not a POST request or file upload failed
    return render_template("upload.html")

@app.route("/processing", methods=["GET"])
def process_uploaded_file():
    if 'filename' not in request.args:
        return "No filename provided in the request", 400
    filename = request.args['filename']
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)

    if not os.path.exists(file_path):
        print(f"File does not exist: {file_path}")
        return redirect(url_for('index'))

    print(f"Processing file: {file_path}")
    created_files = Pipeline2.process_video(file_path)
    print(f"File processed, created files: {created_files}")

    # Redirect to the /result route with the filenames of the created files as query parameters
    return redirect(url_for('show_results', **created_files))

@app.route("/result", methods=["GET"])
def show_results():
    if 'audio_output' not in request.args or 'json_output' not in request.args or 'script_output' not in request.args:
        return "No filenames provided in the request", 400
    audio_output = request.args['audio_output']
    json_output = request.args['json_output']
    script_output = request.args['script_output']

     # Read the json_output file
    json_output_path = os.path.join(app.config["UPLOAD_FOLDER"], json_output)
    with open(json_output_path, 'r') as f:
        json_output_data = json.load(f)  # This is the JSON data read from the json_output file

    # Read the script_output file
    script_output_path = os.path.join(app.config["UPLOAD_FOLDER"], script_output)
    with open(script_output_path, 'r') as f:
        script_output_data = json.load(f)  # This is the JSON data read from the script_output file
    
    return render_template("result.html",
        audio_output = url_for("download_file", filename=audio_output),
        json_output = url_for("download_file", filename=json_output),
        script_output = url_for("download_file", filename=script_output),
        json_output_data = json_output_data,  # Pass the json_output data to the template
        script_output_data = script_output_data,  # Pass the script_output data to the template
    )

if __name__ == "__main__":
    app.run(debug=True)
