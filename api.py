from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
import os
import subprocess
import requests
import json
from datetime import datetime



# try:
#     import Image
# except ImportError:
#     from PIL import Image
# import pytesseract




app = FastAPI()

class TaskRequest(BaseModel):
    task: str
    data: str = None
    path: str = None

def install_uv_if_required():
    try:
        subprocess.run(["uv", "--version"], check=True, capture_output=True)
    except FileNotFoundError:
        subprocess.run(["pip", "install", "uv"], check=True)

def run_datagen(user_email: str) -> str:
    script_url = "https://raw.githubusercontent.com/sanand0/tools-in-data-science-public/tds-2025-01/project-1/datagen.py"
    script_path = "datagen.py"
    
    response = requests.get(script_url)
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to download datagen.py")
    
    with open(script_path, "w", encoding="utf-8") as file:
        file.write(response.text)
    
    install_uv_if_required()
    
    try:
        subprocess.run(["python", script_path, user_email], check=True)
        return "datagen.py executed successfully."
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Error executing script: {str(e)}")

def install_prettier():
    try:
        subprocess.run(["prettier", "--version"], check=True, capture_output=True)
    except FileNotFoundError:
        subprocess.run(["npm", "install", "-g", "prettier@3.4.2"], check=True)

def format_file_with_prettier(file_path: str) -> str:
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    install_prettier()
    try:
        subprocess.run(["prettier", "--write", file_path], check=True)
        return f"Formatted {file_path} successfully."
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Error formatting file: {str(e)}")

def count_wednesdays_in_file(file_path: str, output_path: str) -> str:
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            dates = file.readlines()
        
        wednesday_count = 0
        for date in dates:
            date_str = date.strip()
            try:
                parsed_date = datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                try:
                    parsed_date = datetime.strptime(date_str, "%Y/%m/%d %H:%M:%S")
                except ValueError:
                    continue  # Skip invalid lines
            
            if parsed_date.weekday() == 2:
                wednesday_count += 1
        
        with open(output_path, "w", encoding="utf-8") as output_file:
            output_file.write(str(wednesday_count))
        
        return f"Counted {wednesday_count} Wednesdays and saved to {output_path}."
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

def sort_contacts(file_path: str, output_path: str) -> str:
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            contacts = json.load(file)
        
        if not isinstance(contacts, list):
            raise HTTPException(status_code=400, detail="Invalid contacts.json format")
        
        sorted_contacts = sorted(contacts, key=lambda c: (c.get("last_name", ""), c.get("first_name", "")))
        
        with open(output_path, "w", encoding="utf-8") as output_file:
            json.dump(sorted_contacts, output_file, indent=4)
        
        return f"Sorted contacts and saved to {output_path}."
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing contacts file: {str(e)}")

def extract_recent_logs(log_dir: str, output_path: str) -> str:
    if not os.path.isdir(log_dir):
        raise HTTPException(status_code=404, detail="Log directory not found")
    
    try:
        log_files = sorted(
            [os.path.join(log_dir, f) for f in os.listdir(log_dir) if f.endswith(".log")],
            key=os.path.getmtime,
            reverse=True
        )[:10]
        
        recent_logs = []
        for log_file in log_files:
            with open(log_file, "r", encoding="utf-8") as f:
                first_line = f.readline().strip()
                recent_logs.append(first_line)
        
        with open(output_path, "w", encoding="utf-8") as output_file:
            output_file.write("\n".join(recent_logs))
        
        return f"Extracted recent logs and saved to {output_path}."
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing logs: {str(e)}")

def index_markdown_titles(doc_dir: str, output_path: str) -> str:
    if not os.path.isdir(doc_dir):
        raise HTTPException(status_code=404, detail="Docs directory not found")
    
    index = {}
    for root, _, files in os.walk(doc_dir):
        for file in files:
            if file.endswith(".md"):
                file_path = os.path.join(root, file)
                with open(file_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.startswith("# "):
                            index[file] = line[2:].strip()
                            break
    
    with open(output_path, "w", encoding="utf-8") as output_file:
        json.dump(index, output_file, indent=4)
    
    return f"Indexed Markdown files and saved to {output_path}."

@app.post("/run")
def run_task(task: str, data: str = None, path: str = None):
    try:
        if task.lower() == "run datagen" and data:
            result = run_datagen(data)
        elif task.lower() == "format file":
            result = format_file_with_prettier(path)
        elif task.lower() == "count wednesdays":
            result = count_wednesdays_in_file("/data/dates.txt", "/data/dates-wednesdays.txt")
        elif task.lower() == "sort contacts":
            result = sort_contacts("/data/contacts.json", "/data/contacts-sorted.json")
        elif task.lower() == "extract recent logs":
            result = extract_recent_logs("/data/logs", "/data/logs-recent.txt")
        elif task.lower() == "index markdown titles":
            result = index_markdown_titles("/data/docs", "/data/docs/index.json")
        else:
            raise HTTPException(status_code=400, detail="Unsupported task")
        
        return {"status": "success", "result": result}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
