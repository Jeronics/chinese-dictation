#!/usr/bin/env python3
"""
Simple Color Palette Visualizer
Creates a clean, minimal HTML display of CSS colors.
"""

import re
import os
from collections import defaultdict

def extract_css_colors(css_file_path: str):
    """Extract color variables from CSS file."""
    if not os.path.exists(css_file_path):
        print(f"Error: CSS file not found at {css_file_path}")
        return {}
    
    with open(css_file_path, 'r', encoding='utf-8') as file:
        css_content = file.read()
    
    # Pattern to match CSS custom properties (variables)
    var_pattern = r'--([^:]+):\s*([^;]+);'
    matches = re.findall(var_pattern, css_content)
    
    # Group colors by category
    color_categories = defaultdict(list)
    
    for var_name, value in matches:
        value = value.strip()
        
        # Check if it's a hex color
        if re.match(r'^#[0-9a-fA-F]{3,8}$', value):
            category = categorize_color(var_name)
            color_categories[category].append((var_name, value))
    
    return color_categories

def categorize_color(var_name: str) -> str:
    """Categorize color variables based on their names."""
    var_lower = var_name.lower()
    
    if any(word in var_lower for word in ['bg', 'background']):
        return 'Background Colors'
    elif any(word in var_lower for word in ['text']):
        return 'Text Colors'
    elif any(word in var_lower for word in ['accent']):
        return 'Accent Colors'
    elif any(word in var_lower for word in ['status']):
        return 'Status Colors'
    elif any(word in var_lower for word in ['border']):
        return 'Border Colors'
    else:
        return 'Other Colors'

def group_accent_colors(colors):
    """Group accent colors with their hover states."""
    base_colors = {}
    hover_colors = {}
    
    for var_name, color_value in colors:
        if var_name.endswith('-hover'):
            base_name = var_name.replace('-hover', '')
            hover_colors[base_name] = (var_name, color_value)
        else:
            base_colors[var_name] = (var_name, color_value)
    
    # Create pairs
    color_pairs = []
    for base_name, (base_var, base_color) in base_colors.items():
        if base_name in hover_colors:
            hover_var, hover_color = hover_colors[base_name]
            color_pairs.append([
                (base_var, base_color),
                (hover_var, hover_color)
            ])
        else:
            color_pairs.append([(base_var, base_color)])
    
    return color_pairs

def generate_simple_html(color_categories):
    """Generate simple HTML with color swatches."""
    html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CSS Color Palette</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background-color: #2a2a2a;
            margin: 0;
            padding: 40px 20px;
            color: #ffffff;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        h1 {
            text-align: center;
            margin-bottom: 40px;
            font-size: 2.5em;
            color: #ffffff;
        }
        
        .palette {
            background-color: #3a3a3a;
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
        }
        
        .palette-name {
            font-size: 1.5em;
            font-weight: 600;
            margin-bottom: 20px;
            color: #ffffff;
            text-align: center;
        }
        
        .color-row {
            display: flex;
            gap: 0;
            justify-content: center;
            flex-wrap: nowrap;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
        }
        
        .color-pair {
            display: flex;
            flex: 1;
            min-width: 160px;
        }
        
        .color-swatch {
            flex: 1;
            min-width: 80px;
            height: 80px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 9px;
            font-weight: bold;
            color: #000;
            text-shadow: 0 1px 2px rgba(255, 255, 255, 0.5);
            transition: transform 0.2s ease;
            position: relative;
            cursor: pointer;
        }
        
        .color-swatch:hover {
            transform: scale(1.02);
            z-index: 10;
        }
        
        .color-swatch.light-text {
            color: #ffffff;
            text-shadow: 0 1px 2px rgba(0, 0, 0, 0.8);
        }
        
        .color-swatch .hex-code {
            font-size: 10px;
            font-weight: bold;
        }
        
        .color-swatch .var-name {
            position: absolute;
            top: 3px;
            left: 50%;
            transform: translateX(-50%);
            font-size: 7px;
            opacity: 0.7;
            white-space: nowrap;
            max-width: 80px;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        
        .color-swatch .hover-label {
            position: absolute;
            bottom: 3px;
            left: 50%;
            transform: translateX(-50%);
            font-size: 6px;
            opacity: 0.6;
            white-space: nowrap;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>CSS Color Palette</h1>
"""
    
    for category, colors in color_categories.items():
        html += f"""
        <div class="palette">
            <div class="palette-name">{category}</div>
            <div class="color-row">
"""
        
        if category == 'Accent Colors':
            # Group accent colors with their hover states
            color_pairs = group_accent_colors(colors)
            
            for pair in color_pairs:
                html += '<div class="color-pair">'
                
                for var_name, color_value in pair:
                    # Determine text color for contrast
                    hex_color = color_value.lstrip('#')
                    if len(hex_color) == 3:
                        hex_color = ''.join([c*2 for c in hex_color])
                    
                    r = int(hex_color[0:2], 16)
                    g = int(hex_color[2:4], 16)
                    b = int(hex_color[4:6], 16)
                    
                    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
                    text_class = "light-text" if luminance < 0.5 else ""
                    
                    # Determine if this is a hover color
                    hover_label = "HOVER" if var_name.endswith('-hover') else ""
                    
                    html += f"""
                        <div class="color-swatch {text_class}" style="background-color: {color_value};" title="{var_name}">
                            <div class="var-name">{var_name.replace('-hover', '')}</div>
                            <div class="hex-code">{color_value[1:].upper()}</div>
                            <div class="hover-label">{hover_label}</div>
                        </div>
"""
                
                html += '</div>'
        else:
            # Regular display for non-accent colors
            for var_name, color_value in colors:
                # Determine text color for contrast
                hex_color = color_value.lstrip('#')
                if len(hex_color) == 3:
                    hex_color = ''.join([c*2 for c in hex_color])
                
                r = int(hex_color[0:2], 16)
                g = int(hex_color[2:4], 16)
                b = int(hex_color[4:6], 16)
                
                luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
                text_class = "light-text" if luminance < 0.5 else ""
                
                html += f"""
                    <div class="color-swatch {text_class}" style="background-color: {color_value};" title="{var_name}">
                        <div class="var-name">{var_name}</div>
                        <div class="hex-code">{color_value[1:].upper()}</div>
                    </div>
"""
        
        html += """
            </div>
        </div>
"""
    
    html += """
    </div>
</body> 
</html>
"""
    
    return html

def main():
    """Main function."""
    css_file = "static/style.css"
    output_file = "developer_tools/simple_color_palette.html"
    
    print("🔍 Extracting colors from CSS file...")
    color_categories = extract_css_colors(css_file)
    
    if color_categories:
        print("🎨 Generating simple color palette...")
        html_content = generate_simple_html(color_categories)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ Simple HTML file generated: {output_file}")
        print("🌐 Open this file in your browser to see the color palette!")
        
        # Summary
        total_colors = sum(len(colors) for colors in color_categories.values())
        print(f"\n📊 Found {total_colors} colors across {len(color_categories)} categories")
        
        # Show what categories we found
        for category, colors in color_categories.items():
            print(f"   - {category}: {len(colors)} colors")
    else:
        print("❌ No color variables found in the CSS file.")

if __name__ == "__main__":
    main() 