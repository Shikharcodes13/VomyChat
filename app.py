import os
import pandas as pd
import google.generativeai as genai
import logging
from chardet.universaldetector import UniversalDetector

logging.basicConfig(
    filename="modification_log.log",
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
)

def log_action(action):
    logging.info(action)

GENAI_API_KEY = "AIzaSyBD1zR7yZQBTQgoIDVXfvQLl_2XH_2D4I4"
genai.configure(api_key=GENAI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

def parse_instructions(user_prompt):
    template = (
        "You are an AI that generates Python code snippets for manipulating Pandas DataFrames. "
        "The user will specify an operation to perform, such as adding columns, filtering rows, "
        "removing duplicates, or dropping columns. Your task is to generate only the Pandas code "
        "snippet that performs the requested operation on a DataFrame named 'df'. "
        "Do not include any descriptions, just the Python code snippet."
    )
    full_prompt = f"{template}\n\nUser request: {user_prompt}"
    response = model.generate_content(full_prompt)
    code_snippet = response.text.strip().strip('```').replace("python", "").strip()
    
    print(code_snippet)
    return code_snippet

def execute_modifications(df, instructions):
    try:
        df = df.drop_duplicates()
        log_action(f"Removed duplicates from the DataFrame.")
        
        local_vars = {"df": df}
        exec(instructions, {}, local_vars)
        df = local_vars["df"]
        log_action(f"Executed the following Pandas operation: {instructions}")
    except Exception as e:
        log_action(f"Error executing the instruction: {instructions}. Error: {str(e)}")
    return df

def modify_files(input_directory, output_directory, instructions, individual_commands=False):
    if not os.path.exists(input_directory):
        raise FileNotFoundError("Input directory does not exist.")

    os.makedirs(output_directory, exist_ok=True)

    for file_name in os.listdir(input_directory):
        file_path = os.path.join(input_directory, file_name)
        if not os.path.isfile(file_path):
            continue

        try:
            if file_name.endswith(".csv"):
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

        if individual_commands:
            user_instructions = input(f"Enter the instructions for modifying the file {file_name}: ").strip()

        else:
            user_instructions = instructions

        try:
            generated_query = parse_instructions(user_instructions)
            log_action(f"Generated query for file {file_name}: {generated_query}")
        except Exception as e:
            log_action(f"Error parsing instructions for file {file_name}: {str(e)}")
            continue

        try:
            df = execute_modifications(df, generated_query)
            log_action(f"Executed modifications successfully for file {file_name}.")
        except Exception as e:
            log_action(f"Error executing modifications for file {file_name}: {str(e)}")
            continue

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
    input_dir = r"C:\Users\hp\OneDrive\Desktop\Vomy Chat\input_directory"
    output_dir = r"C:\Users\hp\OneDrive\Desktop\Vomy Chat\output_directory"

    command_choice = input("Do you want to apply the same command to all files or individual commands per file? (Enter 'all' or 'individual'): ").strip().lower()

    if command_choice == "individual":
        user_instructions = None
    else:
        user_instructions = input("Enter the instructions for modifying the files: ").strip()

    try:
        modify_files(input_dir, output_dir, user_instructions, individual_commands=(command_choice == "individual"))
        print("All files processed. Check the output directory.")
    except Exception as e:
        print(f"Error: {str(e)}")
