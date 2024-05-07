# mandelbrot-pyopengl-pyqt5
Mandelbrot set implementation using PyOpenGL and PyQt5

## Features

- **Interactive Zooming**: Use your mouse wheel to zoom in and out of the Mandelbrot set.
- **Panning**: Click and drag to move around the fractal.
- **Dynamic Iteration Adjustment**: Automatically adjusts the number of iterations based on the zoom level to enhance detail.
- **Real-time Rendering**: Utilizes the GPU for real-time fractal rendering.

## Prerequisites

Before you begin, ensure you have met the following requirements:
- Python 3.6 or higher
- A compatible OpenGL driver and a GPU that supports at least OpenGL 4.3
- Operating System: Windows, Linux, or macOS

## Installation

To install the dependencies for this project, follow these steps:

```bash
# Clone the repository
git clone https://github.com/yourgithubusername/mandelbrot-explorer.git
cd mandelbrot-explorer

# Set up a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`

# Install the required packages
pip install -r requirements.txt
