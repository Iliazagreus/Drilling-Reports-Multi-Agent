# -*- coding: utf-8 -*-

""" TO DO:
1. STRICT MODE - JSON
2. Add NPT to the table
2. Finish prompt but adding parameters f string
3. Add more feautures from reports such as bit types
4. API key enviroment?

"""

""" **IMPORTANT:** when using JSON mode, you **must** also instruct the model to
              produce JSON yourself via a system or user message."""

"""temperature: What sampling temperature to use, between 0 and 2. Higher values like 0.8 will
              make the output more random, while lower values like 0.2 will make it more
              focused and deterministic. We generally recommend altering this or top_p but not
              both"""


"""# Extracting and Preprocessing"""

# pip install pdfplumber

# from google.colab import drive
# drive.mount('/content/drive')

# import os
import re
import pdfplumber
import pandas as pd
import numpy as np

from groq import Groq
from pydantic import BaseModel
import json
from typing import List


def get_report(doc):
   with pdfplumber.open(doc) as pdf:
    date = None

    metrics = []


    date_pattern = re.compile(r'\bDATE\b\D*(\d{2}/\d{2}/\d{4})')
    DATE_F = False

    metrics_pattern = re.compile(r'(DOL|MD/TVD|MD|DFS):\D*(\d+)')

    # Iterate through each page
    columns = ["FROM", "TO", "HRS", "PHASE", "CODE", "NPT", "OPERATIONS"]
    report = pd.DataFrame(columns = columns)
    # Extract table data from the page

    table_settings = {
    "vertical_strategy": "lines",
    "horizontal_strategy": "lines",
    "join_tolerance": 8,
    }

    table = pdf.pages[0].extract_table()
    
    RP_FLAG = len(table) + 1

    for row_number,row in enumerate(table):
      cleaned_row = [x if x != '' else 'None' for x in row if x is not None]


      #extracting date
      if not(DATE_F):
        if any("DATE" in elem for elem in cleaned_row):
          matches = date_pattern.finditer(" ".join(cleaned_row))
          for match in matches:
            date = match
            DATE_F = True
            break 
          metrics.append(date)

      #extractind DOL,DFS and other metrics
      if row_number < 5: #check only top headings
        matches = metrics_pattern.finditer(" ".join(cleaned_row))
        if matches:
          for match in matches:
            metrics.append(match)

      #to parse a very low table, this is the mark when to start
      if "TIME BREAKDOWN" in cleaned_row:
        RP_FLAG = row_number + 2 #have a lag of parsing because of noisy row

      #parse of the table
      if RP_FLAG <= row_number:
        # print(cleaned_row)
        if all(x == "None" for x in cleaned_row):
          break
        report.loc[len(report)] = cleaned_row


    return metrics,report

# for file in files:
#   metrics, report = get_report(file)
#   break
# metrics,report

# report

"""# LLM"""

# !pip install tensorflow --upgrade

def DDR_sum(doc, strict_mode = False):

    metrics,report = get_report(doc)
    csv_string = report.to_csv(index=False)

    date = metrics[0].group(1)
    month, day, year = date.split('/')
    date = f"{year}-{month}-{day}"
    # content = "Analyse the table in terms of Key Points and Time Breakdowns. \n\n" + csv_string

    # content = """
    # You are a oil ddr analyst

    # briefly summarize the key points from the following table that is from an oil ddr

    # Dont breakdown by time intervals

    # the summary should have numerical data that can be cross referenced with time series for further analysis to be done by an sme
    # """ + csv_string

    with open('Groq.txt', 'r') as file:
      lines = file.readlines()

    client = Groq(api_key=lines[0])

    if strict_mode:

      class Summarization(BaseModel):
          summary_of_operation: str
          time_table: List[str]
          key_events: List[str]  
          drilling_progress: str 

      system_instruction = f"""

You are the Expert Analyst specializing in Drilling Reports at a leading Oil and Gas company.

You will analyze the Daily Drilling Report (DDR) which includes a table of events and various operational parameters. Your task is to succinctly summarize the key points from the report, focusing particularly on numerical data that are crucial for drilling operations. This summary will aid cross-referencing with Time Series data and facilitate further analysis by an SME (Subject Matter Expert).

The JSON schema you must follow includes:
- summary_of_operation: Provide a concise summary in 1-2 sentences of the activities during the reporting period.
- time_table: List all events that occurred during the day with their respective durations, formatted as "Event: Duration (hours)". Ensure each entry is brief but informative, accurately reflecting the time spent on each activity.
- key_events: Identify and list the critical events of the day, including relevant numerical values where applicable.
- drilling_progress: Provide a brief comparative analysis of the drilling progress from the start to the end of the given report period.
      
      The JSON object must use the schema: {json.dumps(Summarization.model_json_schema(), indent=2)}

      """     
#  Ensure your output strictly adheres to the following JSON structure, filling each field accurately.
      content = f"""

      Parameters:
      TVD (Total Vertical Depth) - {metrics[3].group(2)}

      The table in csv format that presented below corresponds to events that happened that day. Where column "Operations" is a description of corresponding event with "CODE" tag. "NPT" stands for Non production time.
      """ + csv_string

      chat_completion = client.chat.completions.create(
        messages=[
          {
              "role": "system",
              "content": system_instruction
          },
          
          {
              "role": "user",
              "content": content,
          }
        ],
        model="llama3-70b-8192",
        # model="mixtral-8x7b-32768",
       temperature=0,
       stream=False,
        # Enable JSON mode by setting the response format
       response_format={"type": "json_object"},
       
    )
    # return chat_completion.choices[0].message.content
      # answer = chat_completion.choices[0].message.content
      answer = Summarization.model_validate_json(chat_completion.choices[0].message.content)


      def print_summary(summary: Summarization) -> str:
          output = []

          output.append("**Summary of Operation:**")
          output.append(summary.summary_of_operation)

          output.append("\n**Time Table:**")
          for event in summary.time_table:
              output.append(f"- {event}")

          output.append("\n**Key Events:**")
          for event in summary.key_events:
              output.append(f"- {event}")

          output.append("\n**Drilling Progress:**")
          output.append(summary.drilling_progress)

          return "\n".join(output)

      return date, print_summary(answer)
    
    
    else:

      system_instruction = """

      You are the Expert Analyst specializing in Drilling Reports in the Best Oil and Gas company in the world.

      You will be given the Daily Drilling Report (DDR) with table of events and necessary parameters of current reports.

      """

      # tvd = "None"
      # for match in metrics:
      #   if "TVD" in match.group():
      #     tvd = match.group(2)
      
      # print(tvd)
      

      content = f"""

      Parameters:
      TVD (Total Vertical Depth) - {metrics[3].group(2)}

      The table in csv format that presented below corresponds to events that happened that day. Where column "Operations" is a description of corresponding event with "CODE" tag. "NPT" stands for Non production time.

      Briefly summarize the key points from the report. Write the key points from the report. The summary should have numerical data that can be cross referenced with Time Series and for further analysis to be done by an SME(Subject Matter Expert).
      Don't write ANY prelude
      """ + csv_string



      chat_completion = client.chat.completions.create(
          messages=[
            {
                "role": "system",
                "content": system_instruction
            },
            
            {
                "role": "user",
                "content": content,
            }
          ],
          model="llama3-70b-8192",
        temperature=0.1,
      )

      return date, chat_completion.choices[0].message.content


if __name__ == "__main__":
    doc = "test2.pdf"

    metrics, report = (get_report(doc))
    output = DDR_sum(doc, strict_mode=True)
    print(output[1])
