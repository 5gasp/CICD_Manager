from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import yaml
import os
import string
import random

app = FastAPI()

# Folder where you want to save the YAML files
PROMETHEUS_TARGETS_FOLDER = os.getenv("PROMETHEUS_TARGETS_FOLDER", "../prometheus/targets")

# Maek sure the folder exists
if not os.path.exists(PROMETHEUS_TARGETS_FOLDER):
    raise RuntimeError(f"Targets folder does not exist: {PROMETHEUS_TARGETS_FOLDER}")

class JobTargets(BaseModel):
    job_name: str
    targets: List[str]

@app.post("/targets")
async def create_target_yaml(payload: JobTargets):
    # Compose the data structure for YAML
    data = [{
        "targets": payload.targets,
        "labels": {"job": payload.job_name}
    }]
    
    # File name based on job_name (sanitize if needed)
    target_filename = payload.job_name + "_" + ''.join(random.choice(string.ascii_letters) for _ in range(5)) + ".yaml"    
    filepath = os.path.join(PROMETHEUS_TARGETS_FOLDER, target_filename)
    
    # Save YAML file
    try:
        with open(filepath, "w") as f:
            yaml.dump(data, f, default_flow_style=False)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error writing file: {e}")
    
    return {"message": f"Targets created for job {payload.job_name}.YAML file created at {filepath}"}
