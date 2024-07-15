# Drilling-Reports-Multi-Agent

# How it works?
<!--
<details>
<summary><span style="font-size:20px;">File A</span> - <span style="font-size:16px;">Overview</span></summary>

### Details for File A
Content or description about what File A includes or its purpose goes here. You can include further Markdown formatting, links, images, or any other relevant information.

</details>
-->


## DDR Agent

This module focuses on extracting data from PDF reports and analyzing it with LLM. It consists of two primary functions:

1. **`get_report(doc)`**: Extracts metrics and operational data from a given PDF document (`doc`). The function uses `pdfplumber` to handle PDF operations, extracting data like dates and specific metrics using regex patterns, and table data based on a defined schema. This table is processed to handle missing values and detect specific rows, which mark sections of the report for detailed parsing.

2. **`DDR_sum(doc)`**: Takes a document as input and uses the `get_report` function to extract data. It then formats this data into a CSV string and constructs a summary with detailed drilling parameters, which can be cross-referenced with time series data. This function integrates a multi-agent system through an API call to generate summaries using a Large Language Model.

## TS Agent

This module is designed for analyzing time series data from drilling logs, focusing on outlier detection, statistical analysis, and data visualization. It employs pandas for data manipulation, Matplotlib and seaborn for plotting, and scipy for statistical functions. The main features of the module include:

1. **`parse_entry(entry)`**: Extracts timestamps, features, and values from log entries using regular expressions. Converts strings to datetime objects and floats, respectively.

2. **`condense_entries(entries, deviation_percent=7)`**: Groups consecutive log entries that share the same feature and are within a specified deviation range into summarized entries with averaged values, helping to identify sustained anomalies.

3. **`split_dataframe_by_sliding_window(df, time_column, window_size, step)`**: Divides the dataframe into overlapping windows, which allows for localized analysis of data over specified intervals, crucial for detecting temporal patterns or anomalies.

4. **Class **`DrillingLogs`**:
   - **Initialization and file handling**: Loads time series data from CSV or Excel files, normalizing timestamps and handling missing values.
   - **`get_correlations(threshold, subset)`**: Identifies highly correlated features based on a user-specified threshold, helping to understand interdependencies within the data.
   - **`get_outliers(date, subset)`**: Detects outliers using IQR, Z-score, and range-based methods, tailored to either all features or a specified subset of important drilling parameters.
   - **`describe(subset)`**: Generates descriptive statistics for the data, offering insights into distribution and central tendencies.
   - **`get_report(date, subset)`**: Compiles a detailed report combining statistical summaries, outlier analysis, and correlations for a given date. Provides both a short and detailed version of the report, which can be directly used for review or further analysis.
   - **`plot_time_series(column_name)`**: Plots the time series for a specified column, visualizing trends and fluctuations over time.
   - **`plot_correlation_heatmap(subset)`**: Generates a heatmap visualizing the correlation matrix of the dataset, aiding in the visual assessment of feature relationships.

 ## Subject Matter Expert (SME) Agent Module

This module is a crucial component of a multi-agent system designed to analyze and integrate drilling report summaries and time series analysis outputs. It consists of two main functions:

1. **`SME_Agent(input_DDR, input_TS)`**: This function takes as input the outputs from the Drilling Data Report (DDR) Agent and Time Series (TS) Agent. It processes these inputs to provide a comprehensive analysis from the perspective of a Subject Matter Expert (SME). The SME is tasked with identifying anomalies, safety concerns, or noteworthy trends from the integrated data, and making recommendations for further action. This analysis is then output to the Writer Agent, which formats it into a consistent, predefined JSON structure for further use.

2. **`Writer_Agent(input_SME)`**: After the SME Agent provides its analysis, the Writer Agent formats this analysis into a structured JSON format. This function uses a predefined JSON schema to ensure that the output adheres to specific standards required for further processing or presentation. The structured output includes detailed sections on alert status, a bigger picture overview, identified anomalies and safety concerns, and recommendations.

