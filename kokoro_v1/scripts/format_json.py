import json
import sys
import os

def format_text_to_json():
    # Get title
    print("Enter the title:")
    title = input().strip()
    
    # Get main content
    print("\nPaste the main content (press Ctrl+D or Ctrl+Z when done):")
    lines = []
    while True:
        try:
            line = input()
            lines.append(line)
        except EOFError:
            break
    
    # Join all lines with newlines
    text = "\n".join(lines)
    
    # Create the JSON structure
    json_data = {
        "title": title,
        "content": text
    }
    
    # Format the JSON with proper escaping
    formatted_json = json.dumps(json_data, indent=4, ensure_ascii=False)
    
    # Get the kokoro_v1 directory path (parent of scripts directory)
    kokoro_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    json_path = os.path.join(kokoro_dir, "wso_content.json")
    
    # Write to file
    with open(json_path, "w", encoding="utf-8") as f:
        f.write(formatted_json)
    
    print(f"\nJSON has been formatted and saved to {json_path}")

if __name__ == "__main__":
    format_text_to_json() 