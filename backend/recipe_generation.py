import os
import json
from openai import OpenAI
from typing import Dict, Optional, List
from dotenv import load_dotenv
from db_connection import get_db_connection

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def chat_with_gpt(messages: List[Dict], model: str = "gpt-3.5-turbo") -> str:
    """
    Send messages to GPT and return the response.
    """
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=1000,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        raise Exception(f"GPT API call failed: {str(e)}")

def generate_recipe_with_gpt(user_directions: str, model: str = "gpt-3.5-turbo") -> Dict:
    """
    Prompts ChatGPT to generate a recipe in JSON format given user directions.
    The response will contain:
        - recipe_name
        - recipe_type (Omnivore, Vegan, Keto, Paleo, or Vegetarian)
        - ingredients (bulleted list)
        - instructions (numbered list)
        - calories per serving
        - fats per serving
        - carbs per serving
        - extra_categories (any other useful tags)
    """
    system_prompt = (
        "You are a helpful assistant that generates recipes in JSON format. "
        "Given user directions, output a recipe as a JSON object with the following fields: "
        "recipe_name, recipe_type (Omnivore, Vegan, Keto, Paleo, or Vegetarian), "
        "ingredients (as a bulleted list), instructions (as a numbered list), "
        "calories (per serving), fat (per serving), carbs (per serving), "
        "and extra_categories (any other useful tags). "
        "Respond ONLY with the JSON object."
        "If you cannot generate a recipe, return an empty JSON object."
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_directions}
    ]
    
    response = chat_with_gpt(messages, model=model)
    
    # Try to parse the response as JSON
    try:
        # Clean the response in case there's extra text
        response = response.strip()
        if response.startswith('```json'):
            response = response[7:]
        if response.endswith('```'):
            response = response[:-3]
        response = response.strip()
        
        recipe_data = json.loads(response)
        return recipe_data
    except json.JSONDecodeError as e:
        raise Exception(f"Failed to parse GPT response as JSON: {str(e)}")

def save_recipe_to_database(recipe_data: Dict, user_id: int) -> Dict:
    """
    Save the generated recipe to the database.
    Returns the saved recipe with its ID.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Extract data from recipe_data, with fallbacks for missing fields
        recipe_name = recipe_data.get('recipe_name', 'Generated Recipe')
        recipe_type = recipe_data.get('recipe_type', 'Omnivore')
        ingredients = recipe_data.get('ingredients', '')
        instructions = recipe_data.get('instructions', '')
        calories = recipe_data.get('calories', 0)
        fat = recipe_data.get('fat', 0.0)
        carbs = recipe_data.get('carbs', 0.0)
        protein = recipe_data.get('protein', 0.0)  # GPT might not provide this
        extra_categories = recipe_data.get('extra_categories', '')
        
        # Insert the recipe
        cursor.execute("""
            INSERT INTO recipes (
                recipe_name, recipe_type, recipe_source, source_user_id,
                recipe_url, ingredients, instructions, directions, calories,
                fat, carbs, protein, extra_categories
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING recipe_id, recipe_name, recipe_type, recipe_source, source_user_id,
                     recipe_url, ingredients, instructions, directions, calories,
                     fat, carbs, protein, extra_categories
        """, (
            recipe_name, recipe_type, 'GPT Generated', user_id,
            None, ingredients, instructions, None, calories,
            fat, carbs, protein, extra_categories
        ))
        
        row = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()
        
        # Return the saved recipe
        return {
            "recipe_id": row[0],
            "recipe_name": row[1],
            "recipe_type": row[2],
            "recipe_source": row[3],
            "source_user_id": row[4],
            "recipe_url": row[5],
            "ingredients": row[6],
            "instructions": row[7],
            "directions": row[8],
            "calories": row[9],
            "fat": float(row[10]) if row[10] is not None else None,
            "carbs": float(row[11]) if row[11] is not None else None,
            "protein": float(row[12]) if row[12] is not None else None,
            "extra_categories": row[13]
        }
        
    except Exception as e:
        raise Exception(f"Failed to save recipe to database: {str(e)}")

def generate_and_save_recipe(user_directions: str, user_id: int, model: str = "gpt-3.5-turbo") -> Dict:
    """
    Complete workflow: generate recipe with GPT and save to database.
    If any step fails, no data is saved and an error is returned.
    """
    try:
        # Step 1: Generate recipe with GPT
        recipe_data = generate_recipe_with_gpt(user_directions, model)
        
        # Step 2: Validate that we got a proper recipe
        if not recipe_data or not recipe_data.get('recipe_name'):
            raise Exception("GPT failed to generate a valid recipe")
        
        # Step 3: Save to database
        saved_recipe = save_recipe_to_database(recipe_data, user_id)
        
        return {
            "success": True,
            "message": "Recipe generated and saved successfully",
            "recipe": saved_recipe
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "recipe": None
        } 