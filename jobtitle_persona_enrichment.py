import pandas as pd
import re
import os.path
from tqdm import tqdm
from pathlib import Path
from ask_chatgpt import *

# Select only rows that contain nonaiveners and no test emails
def filter_emails(df, column_name):
    df = df[~df[column_name].str.contains("@aiven|test", regex=True)]
    return df

# Load the CSV file
path = input("Input the absolute path of the input file with prospects and no persona: ")

# Ensure the path string is treated correctly (removing quotes if any)
path = path.replace('"', '')

# Read the CSV file into a DataFrame
df = pd.read_csv(path)

# Filter out emails from Aiven and test emails
df_filtered = filter_emails(df, 'Email')

# Filter rows where 'Job.Title' is not empty
df_filtered = df_filtered[df_filtered['Job Title'].notna()]

# Persona definition to pass to the API

definition = """You are an assistant with a strong machine learning capability who understands multiple languages including Japanese, and designed to efficiently categorize job titles into one of four distinct customer personas using a sophisticated machine learning approach.
It leverages techniques like fuzzy matching and similarity search to analyze job titles, focusing on attributes such as industry knowledge, required skills, and typical responsibilities.
You operate by receiving a 2-column table: Prospect ID, Job title. You always return data in a comma-separated, four-column table: Prospect ID, Job title, Persona, Persona Certainty.
The Prospect ID for each output row must be the same one that was fed as input. This is crucial.
Persona Certainty must be a number from 0 to 1 with 2 decimals.
The classification is based on the initial input only, without requiring further interaction.
The output columns must be comma-separated and have no leading or trailing symbols. No context will be provided for the output.

The four available personas are:
- Executive: Hold the highest strategic roles in a company. Responsible for the creation of products/services that support the company's strategy and vision and meet the customer needs. In charge of the cloud and open source strategy of the company. Their titles often contain Chief or Officer, also abbreviated as three-letter acronyms like CEO, CTO, etc.

- IT Manager: Makes decisions on platform and infrastructure, have budget control and manage a team. They drive cloud migration, IT modernization and transformation efforts. Responsible for automated platform solutions for internal teams. Typical titles include Head/Director/Manager of Cloud, Infrastructure or Engineering.

- Architect: Specialist in cloud/ platform technologies, provide the “platform as a service” internally to application teams. They participate in business strategy development  making technology a fundamental investment tool to meet the organizations' objectives. Common titles are Cloud Architect, Platform Architect, Data Platform Manager, Principal Engineer

- Developer: Builds features and applications leveraging data infrastructure. Their typical job titles include Software Engineer, Software Architect and Engineering Manager

Job titles that do not conform to any of these four classes (e.g. Consultant, Student, Unemployed, and many more) should be classified as Not a target.
On the basis of those definitions, please classify these individuals job titles by whether they refer to a Developer, an Executive, an IT Manager, an Architect or Not a target. Only 1 category is possible for each job title."""


# Main logic for processing and enriching data
chunk_size = 150  # Modify this based on rate limits or for debugging, 150 fits inside current rate limit
total_rows = len(df_filtered)
chunks = [df_filtered[i:i+chunk_size] for i in range(0, total_rows, chunk_size)]

#Print number of chunks
print("Number of iterations: ", len(chunks))

results = []

for chunk in tqdm(chunks):
    # Clean and prepare data for API call
    chunk['Job Title'] = chunk['Job Title'].apply(lambda x: re.sub(",", " ", x))
    # Prepare the data in the required format for the API call
    job_titles_table = "\n".join([f"{row['Prospect Id']},{row['Job Title']}" for index, row in chunk.iterrows()])
    
    # Construct the full prompt with 'definition' and job titles table, then call the API
    prompt = definition + job_titles_table
    response = ask_chatgpt(prompt)
       
    # Process response and add to results
    results.append(response)

    # Print loop progress


# Combine all results and perform any necessary cleaning or formatting
final_result = "\n".join(results)


# Combine all results into a single DataFrame
results_dfs = [pd.read_csv(pd.compat.StringIO(result)) for result in results]
combined_results_df = pd.concat(results_dfs, ignore_index=True)

# Assuming 'Prospect ID' is the name of the column in df_filtered to match on
# And assuming df_filtered has a 'Prospect ID' column to join on
reconciled_results = pd.merge(df_filtered, combined_results_df, on="Prospect ID", how="inner")

# reconciled_results now contains the inner join of the original filtered DataFrame and the enriched results
# You can inspect the DataFrame by printing it or viewing it in your IDE
print(reconciled_results.head())  # Print the first few rows to check

# To save the reconciled results to a new CSV file:
reconciled_results.to_csv("reconciled_results.csv", index=False)

# Define path of dir to save to
save_path = "C:/Users/Jaime/Documents/Marketing analytics"

# Output results to a file with current date and time in the filename
from datetime import datetime
output_filename = os.path.join(save_path, datetime.now().strftime("Personas %Y-%m-%d %H %M %S.txt"))

with open(output_filename, 'w', encoding='utf-8') as file:
    file.write(final_result)

print(f"Output written to {output_filename}")
