import google.generativeai as genai
import os
import json
from PIL import Image
import io

def analyze_student_list_image(image_bytes):
    """
    Analyzes an image using Gemini to extract Dept, Sem, and Rolls.
    Returns a dict with extracted data or error.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return {"error": "Missing GEMINI_API_KEY in environment variables. Please add it to your .env file."}
        
    genai.configure(api_key=api_key)
    
    # Use flash model for speed
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    try:
        image = Image.open(io.BytesIO(image_bytes))
    except Exception as e:
        return {"error": f"Invalid image format: {str(e)}"}
        
    prompt = """
    You are a data extraction assistant. Analyze this image of a student list.
    Extract the following information:
    1. Department Code (e.g. CSE, EEE, CIVIL). Look for headers or context. Return null if unclear.
    2. Semester Number (Integer 1-8). Look for "1st Semester", "Semester: 1", "L-1 T-1" (1). Return null if unclear.
    3. List of ALL Student Roll Numbers visible. Ignore names.
    
    Return strict JSON format:
    {
        "department_code": "CSE", 
        "semester_number": 1,
        "rolls": ["101", "102", "103"]
    }
    """
    
    try:
        response = model.generate_content([prompt, image])
        # Clean response text (remove markdown code blocks)
        text = response.text.replace('```json', '').replace('```', '').strip()
        data = json.loads(text)
        return data
    except Exception as e:
        return {"error": f"AI Parsing failed: {str(e)}"}
