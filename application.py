from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware  # Add this import
from pydantic import BaseModel
from typing import List, Dict, Any
import uvicorn
import time
import importlib.util
import os
import numpy as np  # For ndarray conversion

# Import master_script
spec = importlib.util.spec_from_file_location("master_script", "master_script.py")
master_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(master_module)

class StorageInput(BaseModel):
    Power: float
    DD: float
    charges_per_year: float
    selected_Tamb: List[float]
    Powercost: float
    interest_rate: float
    project_lifespan: int

class StorageOutput(BaseModel):
    results: Dict[str, Any]  # Any for flexibility
    timings: Dict[str, float]
    console_log: str
    plot_files: Dict[str, str]

def convert_ndarrays_to_lists(obj: Any) -> Any:
    """Recursively convert NumPy arrays to lists for JSON serialization."""
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {k: convert_ndarrays_to_lists(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_ndarrays_to_lists(item) for item in obj]
    else:
        return obj

def execute_master_script(inputs: dict) -> dict:
    print("Executing master script...")
    timings = {}
    overall_start = time.time()
    setup_start = time.time()
    timings['setup'] = time.time() - setup_start
    calc_start = time.time()
    script_results = master_module.run(inputs)
    timings['calculation'] = time.time() - calc_start
    process_start = time.time()
    # Convert ndarrays to lists here
    converted_results = convert_ndarrays_to_lists(script_results['results'])
    script_results['results'] = converted_results
    timings['output_processing'] = time.time() - process_start
    timings['overall'] = time.time() - overall_start
    print("Master script complete.")
    return {
        'results': script_results['results'],
        'timings': timings,
        'console_log': script_results['console_log'],
        'plot_files': script_results.get('plot_files', {})
    }

app = FastAPI(title="Arctic LCOS API")

# Add CORS middleware (allows POST from Streamlit)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://streamlit.io", "https://*.streamlit.app", "*"],  # Add your Streamlit domain; "*" for testing
    allow_credentials=True,
    allow_methods=["*"],  # Allows POST
    allow_headers=["*"],
)

@app.post("/calculate", response_model=StorageOutput)
async def calculate_storage(inputs: StorageInput):
    print("POST /calculate received! Starting execution...")
    try:
        input_dict = inputs.dict()
        exec_result = execute_master_script(input_dict)
        print("POST /calculate complete!")
        return StorageOutput(**exec_result)
    except Exception as e:
        print(f"POST /calculate crashed with error: {type(e).__name__}: {str(e)}")
        import traceback
        print("Full traceback:", traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Execution failed: {str(e)}")

@app.get("/")
async def root():
    return {"message": "API live! POST to /calculate with JSON inputs."}

@app.get("/health")
async def health():
    return {"status": "alive", "timestamp": time.time()}

print("App defined. Starting uvicorn...")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"Binding to port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info", reload=False)
