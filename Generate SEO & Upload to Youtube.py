# @title Generate SEO
import json
from openai import OpenAI
from typing import Dict

# Initialize the OpenAI client
client = OpenAI(api_key="xxx")

def generate_seo_content(video_content: str) -> Dict[str, str]:
    """
    Generates a title, title keywords, additional keywords, and description for a video using OpenAI.

    Args:
        video_content (str): A string containing the video content (e.g., summary, transcript).

    Returns:
        Dict[str, str]: A dictionary containing the generated title, title_keywords, keywords, and description.
    """
    prompt = (
        "You are a YouTube content optimization expert. Based on the following video content, "
        "generate a proper video title, title keywords, additional keywords, and a description. "
        "Return the result as a JSON object with 'title' (a proper YouTube title), "
        "'title_keywords' (comma-separated string), 'keywords' (comma-separated string for tags), "
        "and 'description' keys.\n\n"
        f"Video content:\n{video_content}\n\n"
        "Output format:\n"
        '```json\n{'
        '"title": "A Proper Video Title", '
        '"title_keywords": "keyword1, keyword2, keyword3", '
        '"keywords": "tag1, tag2, tag3", '
        '"description": "Video description here"'
        '}\n```'
    )

    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that returns JSON responses."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=256,
            temperature=0.7,
        )

        generated_text = completion.choices[0].message.content.strip()
        if generated_text.startswith("```json") and generated_text.endswith("```"):
            generated_text = generated_text[7:-3].strip()

        output = json.loads(generated_text)
        return output

    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}")
        print(f"Raw response: {generated_text}")
        return {
            "title": "Error: Unable to Generate Title",
            "title_keywords": "",
            "keywords": "",
            "description": "Error generating description."
        }
    except Exception as e:
        print(f"API error: {e}")
        return {
            "title": "Error: API Failure",
            "title_keywords": "",
            "keywords": "",
            "description": "An error occurred while processing."
        }

# Example usage
if __name__ == "__main__":

    # Generate SEO content
    seo_content = generate_seo_content(final_content)

    # Print the full result
    print("\nGenerated Output:", json.dumps(seo_content, indent=2))

    # Access individual components
    title = seo_content.get("title", "")
    title_keywords = seo_content.get("title_keywords", "")
    keywords = seo_content.get("keywords", "")
    description = seo_content.get("description", "")

    print("\nTitle:", title)
    print("Title Keywords:", title_keywords)
    print("Additional Keywords:", keywords)
    print("Description:", description)

    # Upload parameters
    file_path = "/content/output_sped_up.mp4"
    upload_script = "/content/drive/MyDrive/YouTUBE REDDIT/Upload Colab.py"
    category = "24"
    privacy_status = "public"

    # Format the command string with proper quoting
    command = (
        f'python "{upload_script}" '
        f'--file="{file_path}" '
        f'--title="{title}" '  # Using the proper title instead of keywords
        f'--description="{description}" '
        f'--keywords="{keywords}" '  # Using the additional keywords for tags
        f'--category="{category}" '
        f'--privacyStatus="{privacy_status}"'
    )

    # Execute the command in Jupyter/Colab
    print("\nExecuting command:", command)
    !{command}
