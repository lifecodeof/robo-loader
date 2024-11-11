import pyglet
from pyglet import shapes
from pyglet.text import Label

# Create the window
window = pyglet.window.Window(1920*2, 1080*2, fullscreen=True)

# Create a batch for managing graphics
batch = pyglet.graphics.Batch()

# Create a rectangle shape (just an example for stunning graphics)
rect = shapes.Rectangle(100, 100, 200, 150, color=(50, 50, 255), batch=batch)

# Create a label for animated text
label = Label('Hello, Pyglet!', font_name='Arial', font_size=36, x=400, y=550, anchor_x='center', anchor_y='center', color=(255, 255, 255, 255))

# Define variables for animation
text_speed = 5
rect_speed = 2

# Update function to move the rectangle and text
def update(dt):
    global text_speed, rect_speed
    # Animate text position (move downwards)
    label.y -= text_speed

    # Animate rectangle position (move diagonally)
    rect.x += rect_speed
    rect.y += rect_speed

    # Reset label position when it goes off-screen
    if label.y < -50:
        label.y = 550

    # Reset rectangle position when it goes off-screen
    if rect.x > window.width or rect.y > window.height:
        rect.x, rect.y = 100, 100

# Schedule the update function to be called every frame
pyglet.clock.schedule_interval(update, 1/60.0)

# On draw event, draw everything to the window
@window.event
def on_draw():
    window.clear()
    batch.draw()
    label.draw()

# Run the pyglet app
pyglet.app.run()
