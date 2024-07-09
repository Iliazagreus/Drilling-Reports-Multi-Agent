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
import pandas as pd
import numpy as np

from groq import Groq
from pydantic import BaseModel, field_validator
import json
from typing import List

import DDR_Agent
import TS_Agent

"""
TO DO:

1. Add Date to json.
2. Explain coluns in SME
3. Choose model for writer
"""

"""
JSON:
[Time Period []]
[Sentiment Analysis: []]
[Any anamalies, safety concerns: []]
[Recomendations: []]
"""


def SME_Agent(input_DDR = None , input_TS = None):
  
    system_instruction =   """
    You are the SME (Subject Matter Expert) specializing in drilling operations at a leading Oil and Gas company in the world, you will analyze the provided key information from a Drilling Report alongside key insights from Time Series data, both from the same specific time period.

    Your task is to integrate these data sources to create a comprehensive overview of this time period's operations, focusing on identifying any anomalies, safety concerns, or noteworthy trends. Discuss any potential implications of these findings and recommend whether further attention or action is required from perspective of SME.

    Don't write ANY prelude. Be concise and directly relevant to the task without including extraneous details.
    """

    # system_instruction =   """
    # You are the SME(Subject Matter Expert) Specialist specializing in Drilling Reports in the Best Oil and Gas company in the world.
 
    # You will be given the key infromation from Drilling Report and key insights from Time Series during the same time period.
 
    # You need to analyse it as SME you need to create a bigger picture of these two sources, analyse it. Then write what happened during this time period
    # from your persepctive and do other people need to raise alert or pay attention to something that happend during this time.
    # Don't write ANY prelude.
    # """

    #[!] TO DO add descriptions of columns for each instances
    content = f"""

    Drilling Report:
    {input_DDR}
    Time Series:
    {input_TS}

    """


    with open('Groq.txt', 'r') as file:
        lines = file.readlines()


    client = Groq(api_key=lines[0])



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

    return chat_completion.choices[0].message.content

def Writer_Agent(input_SME = None):
  
    with open('Groq.txt', 'r') as file:
        lines = file.readlines()


    client = Groq(api_key=lines[0])
    

    class AlertStatus(BaseModel):
        alertness_level: int  # Scale from 1 to 10
        level_description: str  # Descriptive word like "Good" or "Bad"

    class Abstract(BaseModel):
        alertStatus: AlertStatus  # Embedded alert status
        bigger_picture: str  # Short text describing the overall situation
        anomalies_safety_concerns: List[str]  # List of short texts about any anomalies or safety issues
        recommendations: List[str]  # List of short texts containing recommendations



        # @field_validator('sentiment_analysis')
        # def validate_sentiment_analysis(cls, v):
        #     scale, quality = v.split()
        #     if int(scale) < 1 or int(scale) > 10:
        #         raise ValueError("Scale must be between 1 and 10.")
        #     if quality not in ['Bad', 'Good']:
        #         raise ValueError("Quality must be 'Bad' or 'Good'.")
        #     return v

    
    # print(json.dumps(Abstract.model_json_schema(), indent=2))
    
    system_instruction =   f"""
    You are expert writer at a leading oil and gas company in the world, your primary role is to format the SME's drilling report into a standardized JSON format. You are not to add any of your own analysis or information; your task is solely to organize the given data accurately according to our JSON schema.

The JSON schema you must follow includes:
- alertStatus: This should be a number EXACTLY from 1 to 10, where 1 indicates no issues and 10 indicates severe problems requiring immediate attention. The associated level_description should match the alert level, categorized as "Good" (1-5), "Warning" (6-8), and "Bad" (9-10).
- bigger_picture: Provide a concise summary of the overall situation as described in the SME's report.
- anomalies_safety_concerns: List any anomalies or safety concerns mentioned in the SME's report.
- recommendations: Capture any recommendations made by the SME.

Ensure your output strictly adheres to the following JSON structure, filling each field accurately based on the SME's report
The JSON object must use the schema: {json.dumps(Abstract.model_json_schema(), indent=2)}
    
    """
    #[!] TO DO add descriptions of columns for each instances
    content = f"""

    Analysis of SME (Subject Matter Expert):
    {input_SME}

    """



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
    answer = Abstract.model_validate_json(chat_completion.choices[0].message.content)

    def print_abstract(abstract: Abstract):
        print("Alert Status:")
        print(f"- Alertness Level: {abstract.alertStatus.alertness_level}")
        print(f"- Description: {abstract.alertStatus.level_description}")

        print("\nOverall Review:")
        print(abstract.bigger_picture)

        print("\nAnomalies and Safety Concerns:")
        for concern in abstract.anomalies_safety_concerns:
            print(f"- {concern}")

        print("\nRecommendations:")
        for recommendation in abstract.recommendations:
            print(f"- {recommendation}")
    
    print_abstract(answer)



if __name__ == "__main__":

    doc = "test.pdf"
    ts_doc = "10s_intervals.csv"


    # metrics, report = (DDR_Agent.get_report(doc))
    DDR_output = DDR_Agent.DDR_sum(doc)

    TS_report = TS_Agent.DrillingLogs(ts_doc)
    TS_output = TS_report.get_report(subset='important', date = '2020-10-25')

    SME_output = SME_Agent(input_DDR = DDR_output, input_TS=TS_output)
    print(Writer_Agent(SME_output))

    # from typing import List, Optional
    # import json

    # from pydantic import BaseModel
    # from groq import Groq

    # with open('Groq.txt', 'r') as file:
    #     lines = file.readlines()
    # groq = Groq(api_key=lines[0])

    # class Recipe(BaseModel):
    #     recipe_name: str
    #     rating: int
    #     ingredients: List[str]
    #     directions: List[str]

    #     @field_validator('rating')
    #     def validate_sentiment_analysis(cls, v):
    #         if int(v) <=  1:
    #             raise ValueError("The food should be excellent - 5. Choose better recipe")
    #         return v


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
    #         temperature=0,
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
    # print(recipe)
