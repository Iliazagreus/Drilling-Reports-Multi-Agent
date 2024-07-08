# Drilling Logs Analysis

This project provides tools for analyzing drilling logs, including parsing entries, condensing reports, and performing statistical analysis.

## Functions

### `parse_entry(entry)`
Parses a string and extracts timestamp, feature, and value.

**Arguments:**
- `entry` (str): The string to be parsed.

**Returns:**
- `dict`: A dictionary with keys `timestamp`, `feature`, and `value`.

### `condense_entries(entries, deviation_percent)`
Generates a shorter report if the values of the date are consecutive and the features and values are the same or different by no more than `deviation_percent`.

**Arguments:**
- `entries` (list): List of report entries.
- `deviation_percent` (float): The percentage deviation allowed for condensing entries.

**Returns:**
- `list`: A condensed list of entries.

### `split_dataframe_by_sliding_window(time, window_size, step)`
Splits a dataframe into smaller dataframes using a sliding window approach.

**Arguments:**
- `time` (pd.Series): The time series data.
- `window_size` (int): The size of the window.
- `step` (int): The step size for the sliding window.

**Returns:**
- `list`: A list of dataframes.

## DrillingLogs Class

### `get_correlations(subset)`
Computes the correlation values for the features in the dataset.

**Arguments:**
- `subset` (str): Whether to analyze 'all' features or only the 'important' ones.

**Returns:**
- `dict`: A dictionary where the key is the feature and the value is the correlation value.

### `get_outliers(date, subset)`
Identifies outliers in the dataset.

**Arguments:**
- `date` (str): The date for which to identify outliers.
- `subset` (str): Whether to analyze 'all' features or only the 'important' ones.

**Returns:**
- `list`: A list of warnings, each as a string.

### `get_report()`
Combines statistics, outliers, and correlations into one comprehensive report.

**Returns:**
- `str`: The report as a string.

## Getting Started

### Prerequisites

- Python 3.x
- pandas
- numpy
- re
- datetime
- seaborn
- scipy
- matplotlib