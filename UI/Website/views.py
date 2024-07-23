from flask import Blueprint, flash, Response, jsonify, redirect, request, render_template
import os
import DDR_Agent, TS_Agent, SME_Agent
import markdown2 

views = Blueprint('views', __name__, static_folder="static/")
# Upload folder to save uploaded files
upload_folder = os.path.join(os.path.dirname(__file__), 'uploads')

if not os.path.exists(upload_folder):
    os.makedirs(upload_folder)

# The allowed extension types
allowed_ext = {'pdf', 'csv'}

# Check if file extension is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_ext


@views.route("/insights", methods=["POST", "GET"])
def home2():

    # Sequence of actions to take place when upload button pressed
    if request.method == 'POST':
        file_names = []
        output_DDR = ""
        output_TS = ()
        output_DDR_markdown = ""
        output_TS_markdown = ""  
        messages = []
        output_SME =""
        output_FR =""
        dateDDR='2020-10-25' # Default date

        if 'files' not in request.files:
            messages.append("No files part in the request")
            output_DDR= ""
            output_TS= ""
            return jsonify({'messages': messages, 'files': file_names, 'output_DDR': output_DDR, 'output_TS': output_TS})

        files = request.files.getlist('files')
        ddr_files = []
        ts_files = []

        for file in files:
            # Check if files uploaded
            if file.filename == '':
                messages.append("No selected file")
                return jsonify({'messages': messages, 'files': file_names, 'output_DDR': output_DDR, 'output_TS': output_TS})
            # Save files to list and Separate the pdf and csv files
            if file and allowed_file(file.filename):
                file_path = os.path.join(upload_folder, file.filename)
                file.save(file_path)
                file_names.append(file.filename)
                if file.filename.rsplit('.', 1)[1].lower() == 'pdf':
                    ddr_files.append(file_path)
                elif file.filename.rsplit('.', 1)[1].lower() == 'csv':
                    ts_files.append(file_path)  

        # Extract DDR Insights from the pdf files
        for ddr in ddr_files:
            dateDDR, output_DDR = DDR_Agent.DDR_sum(ddr, strict_mode=True)
            output_DDR_markdown = markdown2.markdown(output_DDR)
            print(dateDDR)
            print(output_DDR)
        
        # Extract Time Series Insights from the csv files
        for ts in ts_files:
            output_TS1 = TS_Agent.DrillingLogs(ts)
            output_TS = output_TS1.get_report(subset='important', date= dateDDR)
            output_TS_markdown = markdown2.markdown(output_TS[0])
            print(output_TS[0])

        # When both TS and DDR computed, Extract SME Insights and Abstract Report
        if(output_TS and output_DDR):
            output_SME = SME_Agent.SME_Agent(input_DDR = output_DDR, input_TS=output_TS[1])
            output_SME_markdown = markdown2.markdown(output_SME)
            print(output_SME)
            output_FR, alertness = SME_Agent.Writer_Agent(output_SME)
            output_FR = "**Date:** " + dateDDR + "\n" + output_FR
            output_FR_markdown = markdown2.markdown(output_FR)
            print(output_FR)
            print(alertness)
        
        # Return JSON file to Frontend 
        return jsonify({'messages': messages, 'files': file_names, 'output_DDR': output_DDR_markdown, 'output_TS': output_TS_markdown, 'output_SME': output_SME_markdown, 'output_FR': output_FR_markdown, 'alertness': alertness})

    elif request.method == 'GET':
        return render_template("insights.html")

@views.route("/insightsver", methods=["POST","GET"])
def home():
    # Sequence of actions to take place when upload button pressed
    if request.method == 'POST':
        file_names = []
        output_DDR = ""
        output_TS = ()
        output_DDR_markdown = ""
        output_TS_markdown = ""  
        messages = []
        output_SME =""
        output_FR =""
        dateDDR='2020-10-25' # Default date

        if 'files' not in request.files:
            messages.append("No files part in the request")
            output_DDR= ""
            output_TS= ""
            return jsonify({'messages': messages, 'files': file_names, 'output_DDR': output_DDR, 'output_TS': output_TS})

        files = request.files.getlist('files')
        ddr_files = []
        ts_files = []

        for file in files:
            # Check if files uploaded
            if file.filename == '':
                messages.append("No selected file")
                return jsonify({'messages': messages, 'files': file_names, 'output_DDR': output_DDR, 'output_TS': output_TS})
            # Save files to list and Separate the pdf and csv files
            if file and allowed_file(file.filename):
                file_path = os.path.join(upload_folder, file.filename)
                file.save(file_path)
                file_names.append(file.filename)
                if file.filename.rsplit('.', 1)[1].lower() == 'pdf':
                    ddr_files.append(file_path)
                elif file.filename.rsplit('.', 1)[1].lower() == 'csv':
                    ts_files.append(file_path)  

        # Extract DDR Insights from the pdf files
        for ddr in ddr_files:
            dateDDR, output_DDR = DDR_Agent.DDR_sum(ddr)
            output_DDR_markdown = markdown2.markdown(output_DDR)
            print(dateDDR)
            print(output_DDR)
        
        # Extract Time Series Insights from the csv files
        for ts in ts_files:
            output_TS1 = TS_Agent.DrillingLogs(ts)
            output_TS = output_TS1.get_report(subset='important', date= dateDDR)
            output_TS_markdown = markdown2.markdown(output_TS[0])
            print(output_TS[0])

        # When both TS and DDR computed, Extract SME Insights and Abstract Report
        if(output_TS and output_DDR):
            output_SME = SME_Agent.SME_Agent(input_DDR = output_DDR, input_TS=output_TS[1])
            output_SME_markdown = markdown2.markdown(output_SME)
            print(output_SME)
            output_FR, alertness = SME_Agent.Writer_Agent(output_SME)
            output_FR = "**Date:** " + dateDDR + "\n" + output_FR
            output_FR_markdown = markdown2.markdown(output_FR)
            print(output_FR)
            print(alertness)
        # Return JSON file to Frontend 
        return jsonify({'messages': messages, 'files': file_names, 'output_DDR': output_DDR_markdown, 'output_TS': output_TS_markdown, 'output_SME': output_SME_markdown, 'output_FR': output_FR_markdown, 'alertness': alertness, 'dateDDR': dateDDR})

    elif request.method == 'GET':
        return render_template("insightsver.html")

