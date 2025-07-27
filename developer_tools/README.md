# Developer Tools

This directory contains utility scripts for development and maintenance of the Chinese Dictation application.

## Color Palette Visualizer

### `show_color_palette_simple.py`

A simple utility to visualize the CSS color palette from `static/style.css`.

**Usage:**
```bash
python3 show_color_palette_simple.py
```

**What it does:**
- Extracts all CSS custom properties (variables) from `static/style.css`
- Groups colors by category (Background, Text, Accent, Status, Border)
- Generates an HTML file (`simple_color_palette.html`) with visual color swatches
- Shows accent colors with their hover states side by side
- Displays hex codes and variable names on each color swatch

**Output:**
- Creates `simple_color_palette.html` in the project root
- Opens the file in your default browser to view the color palette

**Features:**
- Clean, minimal design
- Responsive layout
- Hover effects
- Automatic contrast detection for text readability
- Groups related colors (base + hover states)

This is useful for:
- Reviewing the color scheme
- Ensuring color consistency
- Planning UI changes
- Accessibility checking 