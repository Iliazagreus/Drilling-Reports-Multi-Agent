# -*- coding: utf-8 -*-

""" TO DO:
1. STRICT MODE - JSON
2. Add NPT to the table
2. Finish prompt but adding parameters f string
3. Add more feautures from reports such as bit types
4. API key enviroment?

"""


"""# Extracting and Preprocessing"""

# pip install pdfplumber

# from google.colab import drive
# drive.mount('/content/drive')

# import os
import re
import pdfplumber
import pandas as pd
import numpy as np


def get_report(doc):
   with pdfplumber.open(doc) as pdf:
    date = None

    metrics = []


    date_pattern = re.compile(r'\DATE\b\D*(\d{2}/\d{2}/\d{4})')
    DATE_F = False

    metrics_pattern = re.compile(r'(DOL|MD/TVD|MD|DFS):\D*(\d+)')

    # Iterate through each page
    columns = ["FROM", "TO", "HRS", "PHASE", "CODE", "NPT", "OPERATIONS"]
    report = pd.DataFrame(columns = columns)
    # Extract table data from the page

    table = pdf.pages[0].extract_table()
    
    RP_FLAG = len(table) + 1

    for row_number,row in enumerate(table):
      cleaned_row = [x for x in row if x is not None and x != '']

      #extracting date
      if not(DATE_F):
        if any("DATE" in elem for elem in cleaned_row):
          matches = date_pattern.finditer(" ".join(cleaned_row))
          for match in matches:
            date = match.group()
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
        if not(cleaned_row):
          break
        if len(cleaned_row) == 7:
          report.loc[len(report)] = cleaned_row
        else:
          cleaned_row.insert(-1, "None")
          report.loc[len(report)] = cleaned_row


    return metrics,report

# for file in files:
#   metrics, report = get_report(file)
#   break
# metrics,report

# report

"""# LLM"""

# !pip install tensorflow --upgrade

def DDR_sum(doc):

    metrics,report = get_report(doc)
    csv_string = report.to_csv(index=False)
    # content = "Analyse the table in terms of Key Points and Time Breakdowns. \n\n" + csv_string

    # content = """
    # You are a oil ddr analyst

    # briefly summarize the key points from the following table that is from an oil ddr

    # Dont breakdown by time intervals

    # the summary should have numerical data that can be cross referenced with time series for further analysis to be done by an sme
    # """ + csv_string


    content = f"""
    Imagine you are the Expert Analyst specializing in Drilling Reports in the Best Oil and Gas company in the world.

    You were given the Daily Drilling Report (DDR) with table of events and necessary parameters of current reports.

    Parameters:
    TVD (Total Vertical Depth) - {metrics[3].group(2)}

    The table in csv format that presented below corresponds to events that happened that day. Where column "Operations" is a description of corresponding event with "CODE" tag. "NPT" stands for Non production time.

    Briefly summarize the key points from the report. Write the key points from the report. The summary should have numerical data that can be cross referenced with Time Series and for further analysis to be done by an SME(Subject Matter Expert).
    Don't write ANY interlude
    """ + csv_string


    with open('Groq.txt', 'r') as file:
        lines = file.readlines()



    from groq import Groq
    client = Groq(api_key=lines[0])



    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": content,
            }
        ],
        # tempreature=0.1,
        model="llama3-70b-8192",
       temperature=0.1,
    )

    return chat_completion.choices[0].message.content


if __name__ == "__main__":
    doc = "test.pdf"
    output = DDR_sum(doc)
    print(output)

# from typing import List, Optional
# import json

# from pydantic import BaseModel
# from groq import Groq

# groq = Groq(api_key=lines[0])


# # Data model for LLM to generate
# class Ingredient(BaseModel):
#     name: str
#     quantity: str
#     quantity_unit: Optional[str]


# class Recipe(BaseModel):
#     recipe_name: str
#     ingredients: List[Ingredient]
#     directions: List[str]


# def get_recipe(recipe_name: str) -> Recipe:
#     chat_completion = groq.chat.completions.create(
#         messages=[
#             {
#                 "role": "system",
#                 "content": "You are a recipe database that outputs recipes in JSON.\n"
#                 # Pass the json schema to the model. Pretty printing improves results.
#                 f" The JSON object must use the schema: {json.dumps(Recipe.model_json_schema(), indent=2)}",
#             },
#             {
#                 "role": "user",
#                 "content": f"Fetch a recipe for {recipe_name}",
#             },
#         ],
#         model="llama3-8b-8192",
#         temperature=0.1,
#         # Streaming is not supported in JSON mode
#         stream=False,
#         # Enable JSON mode by setting the response format
#         response_format={"type": "json_object"},
#     )
#     return Recipe.model_validate_json(chat_completion.choices[0].message.content)


# def print_recipe(recipe: Recipe):
#     print("Recipe:", recipe.recipe_name)

#     print("\nIngredients:")
#     for ingredient in recipe.ingredients:
#         print(
#             f"- {ingredient.name}: {ingredient.quantity} {ingredient.quantity_unit or ''}"
#         )
#     print("\nDirections:")
#     for step, direction in enumerate(recipe.directions, start=1):
#         print(f"{step}. {direction}")


# recipe = get_recipe("apple pie")
# print_recipe(recipe)

# !pip install accelerate
# !pip install bitsandbytes

#AutoCasualLM

# import transformers
# import accelerate
# import bitsandbytes

# import torch

# from huggingface_hub import login

# # Replace 'YOUR_TOKEN' with your actual Hugging Face access token
# login(token=lines[0])

# model_id = "meta-llama/Meta-Llama-3-8B"



# pipeline = transformers.pipeline(
#     "text-generation",
#     model=model_id,
#     model_kwargs={
#         "torch_dtype": torch.float16,
#         "quantization_config": {"load_in_4bit": True},
#         "low_cpu_mem_usage": True,
#     },
# )

# import transformers
# # from transformers import pipeline
# import torch

# model_id = "meta-llama/Meta-Llama-3-8B-Instruct"

# pipeline = transformers.pipeline(
#     "text-generation",
#     model=model_id,
#     model_kwargs={
#         "torch_dtype": torch.float16,
#         "quantization_config": {"load_in_8bit": True},
#         "low_cpu_mem_usage": True,
#     },
# )
