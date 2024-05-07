# Python Imports
import sys
import os
import ctypes
import numpy as np
from PyQt5.QtWidgets import QApplication, QOpenGLWidget, QLabel, QWidget, QVBoxLayout
from PyQt5.QtCore import QTimer, Qt
from OpenGL.GL.shaders import compileProgram, compileShader
from OpenGL.GL import (
    glClearColor,
    glGenVertexArrays,
    glGenBuffers,
    glBindVertexArray,
    glBufferData,
    glBindBuffer,
    glVertexAttribPointer,
    glEnableVertexAttribArray,
    glGetUniformLocation,
    glUniform1i,
    glViewport,
    glClear,
    glUseProgram,
    glDrawArrays,
    glGetShaderiv,
    glGetShaderInfoLog,
    glGetString,
    glUniform2dv,
    GL_VERTEX_SHADER,
    GL_FRAGMENT_SHADER,
    GL_ARRAY_BUFFER,
    GL_FLOAT,
    GL_FALSE,
    GL_TRUE,
    GL_STATIC_DRAW,
    GL_COLOR_BUFFER_BIT,
    GL_TRIANGLES,
    GL_COMPILE_STATUS,
    GL_EXTENSIONS
)


class OpenGLWidget(QOpenGLWidget):
    def __init__(self, parent=None):
        super(OpenGLWidget, self).__init__(parent)

        # Moves, and changes the PyQt5 widget to fullscreen (as specified in setup_screen function)
        QTimer.singleShot(500, self.setup_screen)

        # Mouse tracking stuff
        self.setMouseTracking(True)
        self.mouse_position = [self.width() / 2, self.height() / 2]

        # Shader stuff
        self.shaders = None
        self.VBO = None  # Vertex Buffer Object
        self.VAO = None  # Vertex Array Object

        # Scale value uniform (zoom magnitude)
        self.init_scale = (800.0, 600.0)  # Make sure the scale is floats and not ints
        self.scale_location = 0  # Location has to match the declared location in fragment shader
        self.scale = None

        # Center location uniform
        self.init_center = [-0.5, 0.0]
        self.center_location = 1  # Location has to match the declared location in fragment shader
        self.center = None

        # Max iterations uniform for Mandelbrot formula
        self.init_max_iter = 600
        self.max_iter_increment_amount = 100
        self.max_iter_limit = 50000
        self.max_iter_location = 2  # Location has to match the declared location in fragment shader
        self.max_iter = None

        # Set up the QLabel to display the zoom level
        self.zoom_label = QLabel(self)
        self.zoom_label.setText("Zoom: 1.00")
        self.zoom_label.move(10, 10)  # Position the label at the top-left corner
        self.zoom_label.setStyleSheet("QLabel { color : white; min-width: 200px;}")  # Set the text color to white for visibility

        # Set up QLabel to display max_iteration level
        self.max_iter_label = QLabel(self)
        self.max_iter_label.setText(f"Max Iterations: {self.init_max_iter}")
        self.max_iter_label.move(10, 30)
        self.max_iter_label.setStyleSheet("QLabel { color : white; min-width: 200px;}")  # Set the text color to white for visibility

    def setup_screen(self):
        screens = QApplication.screens()
        target_screen_index = 1 if len(screens) > 1 else 0  # Moves PyQt5 widget to second screen if it exists
        screen = screens[target_screen_index]
        rect = screen.availableGeometry()
        self.resize(rect.width(), rect.height())
        self.move(rect.left(), rect.top())
        self.debug_screen_info(screen, target_screen_index)

    def debug_screen_info(self, screen, index):
        print(f"Target Screen Index: {index}")
        print(f"Screen Name: {screen.name()}")
        print(f"Screen Resolution: {screen.size().width()}x{screen.size().height()}")
        print(f"Screen Available Geometry: {screen.availableGeometry()}")
        print(f"Widget Position: {self.pos()}")
        print(f"Widget Geometry: {self.geometry()}")

    def mouseMoveEvent(self, event):
        new_mouse_position = [event.x(), event.y()]
        if event.buttons() == Qt.LeftButton:
            # Calculate change in mouse position
            delta_x = new_mouse_position[0] - self.mouse_position[0]
            delta_y = new_mouse_position[1] - self.mouse_position[1]

            # Update center based on deltas
            self.center[0] -= delta_x / self.scale[0]
            self.center[1] += delta_y / self.scale[1]

            # Update uniforms
            self.makeCurrent()
            glUniform2dv(self.center_location, 1, self.center)
            self.update()

        # Update the last known position
        self.mouse_position = new_mouse_position

    def wheelEvent(self, event):
        init_scale = np.array(self.init_scale)

        # Get a scroll amount value
        delta = event.angleDelta().y() / 120.0  # Each step is 15 degrees, typically 120 per notch

        # Update the scale based on scroll direction
        if delta < 0:  # Scroll down = Zoom out
            self.scale *= 0.9
            self.max_iter = min(self.max_iter - self.max_iter_increment_amount, self.max_iter_limit)  # Increment max_iter

        elif delta > 0:  # Scroll up = Zoom in
            self.scale *= 1.1
            self.max_iter = min(self.max_iter + self.max_iter_increment_amount, self.max_iter_limit)  # Decrement max_iter

        # Calculate Zoom Magnitude since start
        zoom_magnitude = self.scale[0] / init_scale[0]
        self.zoom_label.setText(f"Zoom: {zoom_magnitude:.2f}")

        # Increment max_iter
        self.max_iter_label.setText(f"Max Iterations: {self.max_iter}")

        # Update uniforms
        self.makeCurrent()
        glUniform2dv(self.scale_location, 1, self.scale)
        glUniform1i(self.max_iter_location, self.max_iter)

        # Redraw widget
        self.update()

    def check_shader_errors(self, shader, shader_type):
        if glGetShaderiv(shader, GL_COMPILE_STATUS) != GL_TRUE:
            error = glGetShaderInfoLog(shader).decode()
            print(f"Error compiling {shader_type}: {error}")
        else:
            print(f"Shader: {shader_type} is ok!")

    def initializeGL(self):
        glClearColor(0.0, 0.0, 0.0, 1.0)  # Set the background color on frame refresh

        # Confirm if float64 will work in shaders
        extensions = glGetString(GL_EXTENSIONS).decode('utf-8')
        if "GL_ARB_gpu_shader_fp64" in extensions:
            print("Double precision supported")
        else:
            print("Double precision not supported")

        vertex_shader = """
        #version 430
        layout(location=0) in vec2 position;
        void main()
        {
            gl_Position = vec4(position, 0.0, 1.0);
        }
        """

        fragment_shader = """
        #version 430
        layout(location=0) uniform dvec2 scale;
        layout(location=1) uniform dvec2 center;
        layout(location=2) uniform int max_iter;
        out vec4 outColor;

        void main() {
            dvec2 z = dvec2(0.0, 0.0);
            dvec2 c = (dvec2(gl_FragCoord.xy) - 0.5 * scale) / scale.y + center;
            int i;
            for (i = 0; i < max_iter; i++) {
                if (dot(z, z) > 4.0) break;
                z = dvec2(z.x * z.x - z.y * z.y, 2.0 * z.x * z.y) + c;
            }
            if (i == max_iter)
                outColor = vec4(0, 0, 0, 1);
            else {
                float red = 0.5 + 0.5 * cos(3.0 + i * 0.15);
                float green = 0.1 + 0.2 * sin(2.4 * i * 0.42);
                float blue = 0.2 + 0.3 * atan(1.2 + i * 0.32);
                outColor = vec4(red, green, blue, 1.0);
            }
        }
        """

        # Compile Shaders
        self.shaders = compileProgram(
            compileShader(vertex_shader, GL_VERTEX_SHADER),
            compileShader(fragment_shader, GL_FRAGMENT_SHADER)
        )

        # Check if the shaders are good to go
        self.check_shader_errors(compileShader(vertex_shader, GL_VERTEX_SHADER), "Vertex Shader")
        self.check_shader_errors(compileShader(fragment_shader, GL_FRAGMENT_SHADER), "Fragment Shader")

        # Activate the shader program
        glUseProgram(self.shaders)

        # Initialize uniforms
        self.scale = np.array(self.init_scale, dtype=np.float64)
        self.center = np.array([-0.5, 0.0], dtype=np.float64)
        self.max_iter = self.init_max_iter

        # Upload uniforms
        glUniform2dv(self.scale_location, 1, self.scale)
        glUniform2dv(self.center_location, 1, self.center)
        glUniform1i(self.max_iter_location, self.max_iter)

        # The starting canvas
        vertices = np.array([
            -1, -1,  # Vertex 1 (Bottom-left corner)
            1, -1,  # Vertex 2 (Bottom-right corner)
            -1, 1,  # Vertex 3 (Top-left corner)
            -1, 1,  # Vertex 3 (Top-left corner) repeated for drawing second triangle
            1, -1,  # Vertex 2 (Bottom-right corner) repeated for drawing second triangle
            1, 1  # Vertex 4 (Top-right corner)
        ], dtype=np.float32)

        # Create and bind a Vertex Array Object (VAO)
        self.VAO = glGenVertexArrays(1)
        glBindVertexArray(self.VAO)

        # Create and bind a Vertex Buffer Object (VBO)
        self.VBO = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.VBO)
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)

        # Setup vertex attribute pointers
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)

        # Unbind the Vertex Array Object
        glBindVertexArray(0)

    def paintGL(self):
        # Clear the screen to the background color
        glClear(GL_COLOR_BUFFER_BIT)

        # Bind VAO
        glBindVertexArray(self.VAO)

        # Draw the triangle
        glDrawArrays(GL_TRIANGLES, 0, 6)

        # Unbind VAO
        glBindVertexArray(0)

    def resizeGL(self, width, height):
        glViewport(0, 0, width, height)


if __name__ == "__main__":
    try:
        os.environ['QT_QPA_PLATFORM'] = 'wayland'  # If your OS is using wayland, tell PyQt5 to use wayland and not X11
        app = QApplication(sys.argv)
        widget = OpenGLWidget()
        widget.show()
        sys.exit(app.exec_())
    except Exception as e:
        print(f"Encountered error: {e}")
