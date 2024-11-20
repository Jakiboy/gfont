import os
import re
import requests
import sys
from urllib.parse import urlparse
from fontTools.ttLib import TTFont

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
    
    # Extract font-family and other font-face properties
    font_face_pattern = re.compile(
        r"@font-face\s*{\s*"
        r"font-family:\s*'([^']+)';\s*"
        r"(font-style:\s*(\w+);)?\s*"
        r"(font-weight:\s*([\w\d]+);)?\s*"
        r"(font-display:\s*(\w+);)?\s*"
        r"src:\s*url\((https://fonts.gstatic.com/[^)]+)\)\s*format\('([^']+)'\);",
        re.IGNORECASE
    )
    matches = font_face_pattern.findall(content)

    if not matches:
        print("No font-face definitions with valid URLs found in the CSS.")
        return

    # Ensure the output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Parse the font-face rules and download fonts
    font_files = []
    for match in matches:
        font_family, _, font_style, _, font_weight, _, font_display, font_url, font_format = match

        # Use default values if properties are missing
        font_style = font_style or 'normal'
        font_weight = font_weight or '400'
        font_display = font_display or 'swap'

        # Extract a clean name for the font file
        font_name = font_url.split('/')[-1]
        font_name = font_name.replace('?', '_').replace('&', '_')
        font_path = os.path.join(output_dir, font_name)

        # If the font is .ttf, convert it to .woff2
        if font_name.endswith('.ttf'):
            ttf_path = font_path
            download_font(font_url, ttf_path)
            woff2_name = font_name.replace('.ttf', '.woff2')
            woff2_path = os.path.join(output_dir, woff2_name)
            convert_ttf_to_woff2(ttf_path, woff2_path)
            os.remove(ttf_path)  # Remove the original TTF file
            font_files.append({
                "font_family": font_family,
                "font_style": font_style,
                "font_weight": font_weight,
                "font_display": font_display,
                "font_name": woff2_name,
                "font_format": 'woff2'
            })
        else:
            # Download the .woff2 or .woff font directly
            download_font(font_url, font_path)
            font_files.append({
                "font_family": font_family,
                "font_style": font_style,
                "font_weight": font_weight,
                "font_display": font_display,
                "font_name": font_name,
                "font_format": font_format
            })

    # Generate a new CSS file that points to the local font files
    css_filename = os.path.join(output_dir, "local_fonts.css")
    with open(css_filename, 'w') as f:
        f.write("/* Generated CSS for local font files */\n")
        for font in font_files:
            f.write(f"""
@font-face {{
    font-family: '{font["font_family"]}';
    src: url('{font["font_name"]}') format('{font["font_format"]}');
    font-style: {font["font_style"]};
    font-weight: {font["font_weight"]};
    font-display: {font["font_display"]};
}}
""")
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
