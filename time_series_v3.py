import pandas as pd
import matplotlib.pyplot as plt 
import seaborn as sns
import numpy as np
from scipy import stats
from datetime import timedelta
import warnings
import re
from datetime import datetime, timedelta

# Ignore all warnings
warnings.filterwarnings('ignore')


def parse_entry(entry):
    pattern = r"At ([\d-]+\s[\d:]+) (.+?) is out of range with value ([\d.-]+)"
    match = re.match(pattern, entry)
    if match:
        timestamp = datetime.strptime(match.group(1), "%Y-%m-%d %H:%M:%S")
        feature = match.group(2)
        value = float(match.group(3))
        return timestamp, feature, value
    return None

def condense_entries(entries, deviation_percent=7):
    condensed_entries = []
    current_start = None
    current_end = None
    current_feature = None
    current_values = []

    for entry in entries:
        parsed_entry = parse_entry(entry)
        if parsed_entry:
            timestamp, feature, value = parsed_entry

            if current_start is None:
                current_start = timestamp
                current_end = timestamp
                current_feature = feature
                current_values.append(value)
            else:
                if (timestamp == current_end + timedelta(minutes=1) and 
                    feature == current_feature and 
                    (max(current_values + [value]) <= min(current_values + [value]) * (1 + deviation_percent / 100) or
                     max(current_values + [value]) == min(current_values + [value]))):
                    current_end = timestamp
                    current_values.append(value)
                else:
                    mean_value = np.mean(current_values)
                    if current_start == current_end:
                        condensed_entries.append(f"At {current_start} {current_feature} is out of range with value {mean_value:.5f}")
                    else:
                        condensed_entries.append(f"From {current_start} to {current_end} {current_feature} is out of range with value {mean_value:.5f}")
                    current_start = timestamp
                    current_end = timestamp
                    current_feature = feature
                    current_values = [value]

    if current_start:
        mean_value = np.mean(current_values)
        if current_start == current_end:
            condensed_entries.append(f"At {current_start} {current_feature} is out of range with value {mean_value:.5f}")
        else:
            condensed_entries.append(f"From {current_start} to {current_end} {current_feature} is out of range with value {mean_value:.5f}")

    return condensed_entries


def split_dataframe_by_sliding_window(df, time_column='Time', window_size='6H', step='15T'):
        df[time_column] = pd.to_datetime(df[time_column])
        
        df = df.sort_values(by=time_column)
        
        window_size_timedelta = pd.to_timedelta(window_size)
        step_timedelta = pd.to_timedelta(step)
        start_time = df[time_column].min()
        end_time = df[time_column].max()
        
        result = []
        
        while start_time <= end_time:
            window_end_time = start_time + window_size_timedelta
            window_df = df[(df[time_column] >= start_time) & (df[time_column] < window_end_time)]
            
            if not window_df.empty:
                result.append(window_df)
            
            start_time += step_timedelta
        
        return result
class DrillingLogs:

    IMPORTANT_COLUMNS = [
        'Time', 'Flow In', 'Bit RPM',
        'Total Depth', 'Top Drive Torque (ft-lbs)',
        'ROP Depth/Hour',  'Block Position',
        'Weight on Bit', #'Depth Hole TVD'
        'Pit Volume Active',
        'Return Flow', 'Pit G/L Active'
    ]
    
    NUMERICAL_FEATURES= {
        'Block Position': (0, 1000),  # Feet or meters, depending on the rig setup, always positive
        'Weight on Bit': (0, 100),  # Tons, complimentory to hookload
        'Hookload': (50, 600),  # Tons
        'ROP Depth/Hour': (0, 200),  # Feet per hour, derived and computed automatically
        'MWD Gamma (API)': (0, 150),  # API units
        'Top Drive RPM': (0, 300),  # RPM
        'Top Drive Torque (ft-lbs)': (0, 60000),  # Foot-pounds
        'Flow In': (0, 1200),  # Gallons per minute
        'Pump Pressure': (500, 5000),  # PSI
        'SPM Total': (0, 250),  # Strokes per minute
        'Pit Volume Active': (0, 1000),  # Barrels
        'Pit G/L Active': (0, 10),  # Gas/Liquid ratio
        'Gas Total - units': (0, 100),  # Units of gas detection
        'Trip Volume Active': (0, 1000),  # Barrels
        'Trip G/L': (0, 10),  # Gas/Liquid ratio
        'Return Flow': (0, 1000),  # Gallons per minute
        'RES PS 2MHZ 18IN': (0, 2000),  # Ohm-meters
        'RES PS 400KHZ 18IN': (0, 2000),  # Ohm-meters
        'MWD Inclination': (0, 90),  # Degrees
        'MWD Azimuth': (0, 360),  # Degrees
        'H2S 01': (0, 10),  # Parts per million (ppm)
        'RSS Azimuth': (0, 360),  # Degrees
        'Total Depth': (0, 30000),  # Feet
        'Bit Diameter': (4, 20),  # Inches
        'Bit RPM': (0, 200),  # RPM
        'Depth Hole TVD': (0, 30000),  # Feet
        'Differential Pressure': (0, 5000),  # PSI
        'Downhole Torque': (0, 60000),  # Foot-pounds
        'MUD TEMP': (0, 200)  # Degrees Fahrenheit
    }

    CATEGORICAL_FEATURES = {
        'Slips Set': (0, 1),  # Binary, 0 or 1
        'On Bottom': (0, 1),  # Binary, 0 or 1
        'RigMode': (0, 10),  # Categorical, specific to rig operations
        'ROCKIT - On/Off': (0, 1),  # Binary, 0 or 1
        'RigEventCode': (0, 9999),  # Categorical, specific to rig events
        'Drill Mode': (0, 5)  # Categorical, specific to drilling operations
    }



    def __init__(self, file_name):
        if '.csv' in file_name:
            self.df = pd.read_csv(file_name)
            self.df['Time'] = pd.to_datetime(self.df['Time'])
        
        else:
            self.df = pd.read_excel(file_name)
            self.df['Time'] = pd.to_datetime(self.df['Time'])
        
        self.df.replace(-999.25, np.nan, inplace = True)
        self.columns = self.df.columns

    
    

    
    def get_correlations(self, threshold=0.5, subset = 'important'):
        if subset == 'important':
            corr_matrix = self.df[self.IMPORTANT_COLUMNS[1:]].corr()
        elif subset == 'all':
            corr_matrix = self.df[[self.df.columns[1:]]].corr()

        # Dictionary to store pairs of correlated features
        correlated_features = {}

        # Iterate through the correlation matrix
        for i in range(len(corr_matrix.columns)):
            for j in range(i + 1, len(corr_matrix.columns)):
                feature1 = corr_matrix.columns[i]
                feature2 = corr_matrix.columns[j]
                correlation = corr_matrix.iloc[i, j]
                
                # Check if the correlation is above the threshold
                if abs(correlation) >= threshold:
                    correlated_features[(feature1, feature2)] = correlation

        return correlated_features
    
    
    def get_outliers(self, date, subset='important'):
        
        result = []
        d = {
            'important' : self.IMPORTANT_COLUMNS[1:],
            'all' : self.NUMERICAL_FEATURES
        }
        for col in d[subset]:
            temp_df = self.df[['Time', col]]
            filtered_df = temp_df[temp_df['Time'].dt.date == pd.to_datetime(date).date()]
            filtered_df = filtered_df.drop_duplicates(subset='Time')
            series = filtered_df.dropna()
            series_windows = split_dataframe_by_sliding_window(series)
            for s in series_windows:
                # IQR method
                Q1 = s[col].quantile(0.25)
                Q3 = s[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                iqr_outliers = s[(s[col] < lower_bound) | (s[col] > upper_bound)]
                
                # Z-score method
                z_scores = stats.zscore(s[col])
                z_outliers = s[(np.abs(z_scores) > 3)]
        

                # range based method
                range_based_outliers = s[(s[col] < self.NUMERICAL_FEATURES[col][0]) | (s[col] > self.NUMERICAL_FEATURES[col][1])]
                
                final_outliers = pd.merge(iqr_outliers, range_based_outliers, on='Time', how='inner')
                final_outliers.rename(columns = {col + '_x' : col}, inplace=True)
                final_outliers = final_outliers[['Time', col]]

                final_outliers = pd.merge(final_outliers, z_outliers, on='Time', how='inner')
                final_outliers.rename(columns = {col + '_x' : col}, inplace=True)
                final_outliers = final_outliers[['Time', col]]
                
                for index, row in final_outliers.iterrows():
                    result.append(f"At {row['Time']} {col} is out of range with value {row[col]:.3f}")

                
        result_df = pd.DataFrame({'alert' : result})
        result_df.drop_duplicates(inplace=True)

        return list(result_df['alert'])
        
    
    def describe(self, subset = 'all'):
        if subset == 'all':
            return self.df.describe()
        elif subset == 'important':
            return self.df[self.IMPORTANT_COLUMNS].describe()
        
    def get_report(self, date, subset='important'):
        correlations = self.get_correlations(subset=subset)
        outliers = self.get_outliers(subset=subset, date=date)
        stat_df = self.describe(subset=subset)
        report = ''
        list_of_correlations = []
        for k,v in correlations.items():
            list_of_correlations.append(f'Correlation between {k[0]} and {k[1]} is equal to {v:.3f}')
        
        stat_df = self.describe(subset=subset)
        
        for col in stat_df.columns[1:]:
                report += f'** Statistics for {col}: **\n'
                report += f'Mean value = {stat_df[col][1] :.3f}\n'
                report += f'Minimum value = {stat_df[col][2]:.3f}\n'
                report += f'25th percentile = {stat_df[col][3]:.3f}\n'
                report += f'Median = {stat_df[col][4]:.3f}\n'
                report += f'75th percentile = {stat_df[col][5]:.3f}\n'
                report += f'Maximum value = {stat_df[col][6]:.3f}\n'
                report += f'Standard deviation = {stat_df[col][7]:.3f}\n'
                report += '\n'

        report += '\n'

        report += f'** Outliers on date {date} with window_size = 6 hrs and step = 15 min: ** \n'
        report += '\n'.join(condense_entries(outliers))
        
        report += '\n'

        report += f'Correlations between {subset} features:\n'
        report += '\n'.join(list_of_correlations)


        print('Report is ready!')
        return report



    def plot_time_series(self, column_name):
        df = self.df[['Time', column_name]]
        df.dropna(subset=column_name)
        plt.figure(figsize=(10, 6))
        plt.plot(df['Time'], df[column_name], label=f'Time Series for {column_name}')
        plt.xlabel('Date')
        plt.ylabel(column_name)
        plt.title(f'Time Series Plot for {column_name}')
        plt.legend()
        plt.grid(True)
        plt.show()

    def plot_correlation_heatmap(self, subset):
        if subset == 'important':
            plt.figure(figsize=(10, 8))
            sns.heatmap(self.df[[self.IMPORTANT_COLUMNS]].corr(), annot=False, cmap='coolwarm', vmin=-1, vmax=1)
            plt.title('Correlation Heatmap')
            plt.show()

        elif subset == 'all':    
            plt.figure(figsize=(10, 8))
            sns.heatmap(self.df.corr(), annot=False, cmap='coolwarm', vmin=-1, vmax=1)
            plt.title('Correlation Heatmap')
            plt.show()