from PIL import Image, ImageDraw, ImageFont


def draw_text_with_width_limit(draw, text, x_start, x_end, y_position, font, color):
    words = text.split()
    lines = []
    current_line = ''

    for word in words:
        test_line = current_line + word + ' '
        text_width, _ = draw.textsize(test_line, font=font)

        if text_width <= (x_end - x_start):
            current_line = test_line
        else:
            lines.append(current_line.strip())
            current_line = word + ' '

    if current_line:
        lines.append(current_line.strip())

    y = y_position
    for line in lines:
        text_width, _ = draw.textsize(line, font=font)
        x = x_start  # Align text to the left within the boundaries
        draw.text((x, y), line, color, font=font)
        y += font.getsize(line)[1]  # Move to the next line


# Assuming you already have your image and font defined
image = Image.new('RGB', (1200, 200), color='black')
draw = ImageDraw.Draw(image)
TEXT_FONT = ImageFont.truetype('fonts/OpenSans-Regular.ttf', 18)
WHITE_COLOR = (255, 255, 255)

# Example text
text_to_draw = "Your long text here that needs to be broken into lines to fit within the specified width Your long text here that needs to be broken into lines to fit within the specified width Your long text here that needs to be broken into lines to fit within the specified width Your long text here that needs to be broken into lines to fit within the specified width Your long text here that needs to be broken into lines to fit within the specified width Your long text here that needs to be broken into lines to fit within the specified width"

# Define boundaries for text placement
x_start = 65
x_end = 1140
y_position = 50

# Call the function to draw text within the specified width and align to the left
draw_text_with_width_limit(
    draw, text_to_draw, x_start, x_end, y_position, TEXT_FONT, WHITE_COLOR
)

image.show()  # Show the image with the drawn text
