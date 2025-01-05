import os
import pandas as pd
import google.generativeai as genai
import logging
from chardet.universaldetector import UniversalDetector

# Set up logging
logging.basicConfig(
    filename="modification_log.log",
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
)

def log_action(action):
    """Log an action for traceability."""
    logging.info(action)

# Gemini API Setup (replace with your API key)
GENAI_API_KEY = "AIzaSyBD1zR7yZQBTQgoIDVXfvQLl_2XH_2D4I4"
genai.configure(api_key=GENAI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

def parse_instructions(user_prompt):
    """Use Gemini AI to parse user instructions into an SQL query."""
    template = (
        "You are an AI that generates SQL queries to manipulate a database table. "
        "The user will specify an operation to perform, such as adding columns, filtering rows, or removing duplicates. "
        "Your task is to generate only the SQL query that performs the requested operation. "
        "Do not include any code or descriptions, just the SQL query."
    )
    full_prompt = f"{template}\n\nUser request: {user_prompt}"
    response = model.generate_content(full_prompt)
    print(response)
    return response.text

def execute_modifications(df, instructions):
    """Modify the DataFrame based on user instructions."""
    if "DROP COLUMN" in instructions.upper():
        # Extract the column name to drop
        import re
        match = re.search(r"DROP COLUMN (\w+);", instructions, re.IGNORECASE)
        if match:
            column_to_drop = match.group(1)
            if column_to_drop in df.columns:
                df = df.drop(columns=[column_to_drop])
                log_action(f"Column {column_to_drop} dropped successfully.")
            else:
                log_action(f"Column {column_to_drop} does not exist in the DataFrame.")
        else:
            log_action("Failed to parse the column to drop.")
    else:
        log_action("Instruction not implemented for Pandas operations.")
    
    return df

def modify_files(input_directory, output_directory, instructions):
    """Modify CSV/Excel files based on user instructions."""
    if not os.path.exists(input_directory):
        raise FileNotFoundError("Input directory does not exist.")

    os.makedirs(output_directory, exist_ok=True)

    for file_name in os.listdir(input_directory):
        file_path = os.path.join(input_directory, file_name)
        if not os.path.isfile(file_path):
            continue

        # Load file into DataFrame
        try:
            if file_name.endswith(".csv"):
                # Detect encoding
                with open(file_path, 'rb') as f:
                    detector = UniversalDetector()
                    for line in f:
                        detector.feed(line)
                        if detector.done:
                            break
                    detector.close()
                    encoding = detector.result['encoding'] or 'ISO-8859-1'

                df = pd.read_csv(file_path, encoding=encoding)
            elif file_name.endswith(".xlsx"):
                df = pd.read_excel(file_path)
            else:
                log_action(f"Skipped unsupported file: {file_name}")
                continue
        except Exception as e:
            log_action(f"Error loading file {file_name}: {str(e)}")
            continue

        log_action(f"File {file_name} uploaded and loaded successfully.")

        # Parse instructions
        try:
            generated_query = parse_instructions(instructions)
            log_action(f"Generated query for file {file_name}: {generated_query}")
        except Exception as e:
            log_action(f"Error parsing instructions for file {file_name}: {str(e)}")
            continue

        # Execute modifications
        try:
            df = execute_modifications(df, generated_query)
            log_action(f"Executed modifications successfully for file {file_name}.")
        except Exception as e:
            log_action(f"Error executing modifications for file {file_name}: {str(e)}")
            continue

        # Save modified file
        modified_file_path = os.path.join(output_directory, f"modified_{file_name}")
        try:
            if file_name.endswith(".csv"):
                df.to_csv(modified_file_path, index=False)
            else:
                df.to_excel(modified_file_path, index=False)
            log_action(f"Modified file saved as {modified_file_path}.")
        except Exception as e:
            log_action(f"Error saving modified file {file_name}: {str(e)}")
            continue

if __name__ == "__main__":
    # Example usage
    input_dir = r"C:\Users\hp\OneDrive\Desktop\Vomy Chat\input_directory"
    output_dir = r"C:\Users\hp\OneDrive\Desktop\Vomy Chat\output_directory"
    user_instructions = input("Enter the instructions for modifying the files: ").strip()

    try:
        modify_files(input_dir, output_dir, user_instructions)
        print("All files processed. Check the output directory.")
    except Exception as e:
        print(f"Error: {str(e)}")
