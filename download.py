import os
import re
import requests
import sys
from urllib.parse import urlparse
from fontTools.ttLib import TTFont
from fontTools.subset import Subsetter, Options

# Function to download the font
def download_font(url, output_path):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise error for bad responses
        with open(output_path, 'wb') as f:
            f.write(response.content)
        print(f"Font downloaded to: {output_path}")
    except Exception as e:
        print(f"Error downloading {url}: {e}")

# Function to convert TTF to WOFF2
def convert_ttf_to_woff2(ttf_path, woff2_path):
    try:
        font = TTFont(ttf_path)
        font.flavor = 'woff2'
        font.save(woff2_path)
        print(f"Converted {ttf_path} to {woff2_path}")
    except Exception as e:
        print(f"Error converting {ttf_path} to WOFF2: {e}")

# Function to parse the CSS and download fonts
def parse_and_download_font(url, output_dir):
    # Fetch the content from the URL
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise error for bad responses
        content = response.text
    except Exception as e:
        print(f"Error fetching content from {url}: {e}")
        return
    
    # Extract font-family from the CSS using regex
    font_family_pattern = re.compile(r"font-family:\s*'([^']+)';", re.IGNORECASE)
    font_family_match = font_family_pattern.search(content)

    if not font_family_match:
        print("No font-family found in the CSS.")
        return
    
    font_family = font_family_match.group(1)
    print(f"Font family detected: {font_family}")

    # Ensure the output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Regex to match the src URL for font files
    src_pattern = re.compile(r"src:\s*url\((https://fonts.gstatic.com/[^)]+\.woff2)\)\s*format\('woff2'\);|"
                             r"src:\s*url\((https://fonts.gstatic.com/[^)]+\.woff)\)\s*format\('woff'\);|"
                             r"src:\s*url\((https://fonts.gstatic.com/[^)]+\.ttf)\)\s*format\('truetype'\);", re.IGNORECASE)
    matches = src_pattern.findall(content)

    if not matches:
        print("No .woff, .woff2, or .ttf fonts found in the CSS.")
        return

    # Parse the font-face and download the font files
    font_files = []
    for font_urls in matches:
        for font_url in font_urls:
            if font_url:  # Ensure that the match is valid
                # Extract a clean name for the font file
                font_name = font_url.split('/')[-1]
                font_name = font_name.replace('?', '_').replace('&', '_')
                font_path = os.path.join(output_dir, font_name)
                
                # If the font is .ttf, we will convert it to .woff2
                if font_name.endswith('.ttf'):
                    ttf_path = font_path  # Temporary path for TTF
                    download_font(font_url, ttf_path)
                    woff2_name = font_name.replace('.ttf', '.woff2')
                    woff2_path = os.path.join(output_dir, woff2_name)
                    convert_ttf_to_woff2(ttf_path, woff2_path)
                    os.remove(ttf_path)  # Remove the original TTF file
                    font_files.append((woff2_path, woff2_name))
                else:
                    # Download the .woff2 or .woff font directly
                    download_font(font_url, font_path)
                    font_files.append((font_url, font_name))

    # Generate a new CSS file that points to the local font files
    css_filename = os.path.join(output_dir, "local_fonts.css")
    with open(css_filename, 'w') as f:
        f.write("/* Generated CSS for local font files */\n")
        for url, font_name in font_files:
            font_face_rule = f"""
@font-face {{
    font-family: '{font_family}';
    src: url('{font_name}') format('woff2');
    font-display: swap;
}}
"""
            # Check the file extension to update the format in CSS if it's not woff2
            if font_name.endswith('.woff'):
                font_face_rule = font_face_rule.replace('woff2', 'woff')
            elif font_name.endswith('.ttf'):
                font_face_rule = font_face_rule.replace('woff2', 'truetype')
                
            f.write(font_face_rule)
        print(f"CSS file generated: {css_filename}")

# Main function to process the input URL and output folder
def main():
    if len(sys.argv) < 2:
        print("Usage: python download.py <google-font-url>")
        sys.exit(1)

    url = sys.argv[1]  # URL passed as command line argument
    output_dir = 'fonts'  # Directory to save the downloaded fonts

    parse_and_download_font(url, output_dir)

if __name__ == "__main__":
    main()
