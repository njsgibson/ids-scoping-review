import pandas as pd
import os
import asyncio
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from tqdm.asyncio import tqdm
from pathlib import Path

# 1. Load environment variables
load_dotenv()

# 2. Define the Expected Output Structure using Pydantic
class ClassificationResult(BaseModel):
    q1_scope: bool = Field(description="Is this paper in scope? (True/False)")
    q2_overview: bool = Field(description="Is it a definitive overview of a specific initiative? (True/False)")
    q3_diagnostics_frameworks: bool = Field(description="Does it propose macroscopic frameworks OR diagnose structural challenges? (True/False)")
    q4_narratives: bool = Field(description="Does it evaluate or tell the story of an implemented effort? (True/False)")
    rationale: str = Field(
        description="1-4 sentences explaining the answers to the 4 questions. If Q1 is false, explain why it failed the scope gate and do not explain the others."
    )

def load_prompt(filepath: str) -> str:
    """Reads the system prompt from a markdown file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        print(f"CRITICAL ERROR: Prompt file not found at {filepath}")
        exit(1)

# --- ASYNC WORKER FUNCTION ---
async def process_row(index, row, client, system_prompt, df, semaphore, save_lock, pbar, output_path, state):
    """Processes a single row asynchronously using a semaphore to limit concurrency."""
    async with semaphore:
        title = row.get("title", "No Title")
        abstract = row.get("abstract", "No Abstract")
        
        # Skip rows with no abstract
        if pd.isna(abstract) or str(abstract).strip() == "":
            df.at[index, "q1_scope"] = False
            df.at[index, "q2_overview"] = False
            df.at[index, "q3_diagnostics_frameworks"] = False
            df.at[index, "q4_narratives"] = False
            df.at[index, "rationale"] = "Auto-excluded: No abstract provided."
        else:
            user_prompt = f"Title: {title}\n\nAbstract: {abstract}"
            
            try:
                # Use the asynchronous client (.aio)
                response = await client.aio.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=user_prompt,
                    config={
                        'system_instruction': system_prompt,
                        'response_mime_type': 'application/json',
                        'response_schema': ClassificationResult,
                        'temperature': 0.1 
                    }
                )
                
                result = response.parsed
                
                # Map results to dataframe
                df.at[index, "q1_scope"] = result.q1_scope
                df.at[index, "q2_overview"] = result.q2_overview
                df.at[index, "q3_diagnostics_frameworks"] = result.q3_diagnostics_frameworks
                df.at[index, "q4_narratives"] = result.q4_narratives
                df.at[index, "rationale"] = result.rationale
                df.at[index, "error_log"] = "" 
                
            except Exception as e:
                error_msg = f"{type(e).__name__}: {str(e)}"
                tqdm.write(f"\n[!] Error processing row {index}: {error_msg}")
                df.at[index, "error_log"] = error_msg
                df.at[index, "rationale"] = "ERROR during processing."

        # Thread-safe saving: only one coroutine can save the file at a time
        async with save_lock:
            state['completed'] += 1
            # Save progressively every 50 completed records to reduce disk I/O
            if state['completed'] % 50 == 0:
                # Run the synchronous save in a background thread so it doesn't block other API calls
                await asyncio.to_thread(df.to_csv, output_path, index=False)
        
        # Tick the progress bar
        pbar.update(1)

# --- MAIN LOGIC ---
async def async_main():
    project_root = Path(__file__).resolve().parent.parent
    
    if not os.getenv("GEMINI_API_KEY"):
        print("CRITICAL ERROR: GEMINI_API_KEY not found. Please check your .env file.")
        exit(1)

    # Retry logic (handles API hiccups automatically)
    retry_options = types.HttpRetryOptions(
        initial_delay=2.0,            
        attempts=5,                   
        exp_base=2,                   
        http_status_codes=[429, 503, 500]  
    )
    http_options = types.HttpOptions(retry_options=retry_options, timeout=120 * 1000)
    
    client = genai.Client(http_options=http_options)
    
    input_path = project_root / "data" / "02_interim" / "openalex_records_2016_present.csv"
    output_path = project_root / "data" / "02_interim" / "classified_2016_present.csv"
    prompt_path = project_root / "prompts" / "03_classify.md"

    print(f"Loading system prompt from {prompt_path}...")
    system_prompt = load_prompt(str(prompt_path))

    # BULLETPROOF CACHE / RESUME MERGE
    print(f"Loading master input data from {input_path}...")
    try:
        df = pd.read_csv(str(input_path))
    except FileNotFoundError:
        print(f"CRITICAL ERROR: Data file not found at {input_path}")
        exit(1)

    # Ensure classification columns exist
    cols_to_add = {"q1_scope": False, "q2_overview": False, "q3_diagnostics_frameworks": False, "q4_narratives": False, "rationale": "", "error_log": ""}
    for col, default_val in cols_to_add.items():
        if col not in df.columns:
            df[col] = default_val

    if output_path.exists():
        print(f"Found existing progress at {output_path}. Merging completed rows...")
        try:
            progress_df = pd.read_csv(str(output_path))
            df.set_index("openalex_id", inplace=True)
            progress_df.set_index("openalex_id", inplace=True)
            df.update(progress_df)
            df.reset_index(inplace=True)
        except Exception as e:
            print(f"CRITICAL ERROR reading existing output file: {e}")
            exit(1)
    else:
        print("No existing progress found. Starting fresh run.")

    # CALCULATE REMAINING WORK
    def needs_processing(row):
        val = row.get("rationale")
        return not (pd.notna(val) and str(val).strip() not in ["", "ERROR during processing.", "Auto-excluded: No abstract provided."])

    # Filter down to only the rows that need API calls
    rows_to_process = df[df.apply(needs_processing, axis=1)]
    records_to_process = len(rows_to_process)
    completed_records = len(df) - records_to_process
    
    print(f"\nFound {completed_records} completed records in the cache.")
    
    if records_to_process == 0:
        print("All records are already classified! Exiting.")
        return

    print(f"Starting async classification for the remaining {records_to_process} records...")
    
    # CONCURRENCY SETUP
    # Semaphore limits us to 15 concurrent API calls (~400-600 RPM)
    semaphore = asyncio.Semaphore(15) 
    save_lock = asyncio.Lock()
    state = {'completed': 0}
    
    # Create the task queue
    tasks = []
    with tqdm(total=records_to_process, desc="Classifying Abstracts", mininterval=1.0) as pbar:
        for index, row in rows_to_process.iterrows():
            task = asyncio.create_task(
                process_row(index, row, client, system_prompt, df, semaphore, save_lock, pbar, output_path, state)
            )
            tasks.append(task)
            
        # Fire off all tasks concurrently
        await asyncio.gather(*tasks)

    # Final save to ensure the last few records under the % 50 threshold are caught
    df.to_csv(output_path, index=False)
    print(f"\nClassification complete! All results saved to {output_path}")

if __name__ == "__main__":
    # Windows-specific fix for asyncio Event Loop policies
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(async_main())