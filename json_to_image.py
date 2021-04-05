from PIL import Image, ImageDraw, ImageColor, ImageFont
from ast import literal_eval

def get_img_size(table_rows, font, x_pad=0, y_pad=0):
    """ Determines image resolution to fit all text based on table entries.
        @param list: table_rows - a list of strings containing each table entry
        @param ImageFont: font - the font of the text being drawn
        @param int: x_pad - Additional horizontal whitespace padding
        @param int: y_pad - Additional vertical whitespace padding
    """
    longest_line = ""

    for line in table_rows:
        longest_line = line if len(line) > len(longest_line) else longest_line

    x, y = ImageDraw.Draw(Image.new('RGB', (0,0))).textsize(longest_line, font=font)
    size = (x + x_pad, y * len(table_rows) + y_pad)

    return size

def write_line_to_image(image, line, font, pos=(0,0), color="black"):
    """ Writes the given text onto an image at the given position
        @param Image: image - the image to draw on
        @param str: line - The text to be drawn
        @param ImageFont: font - the font of the text being drawn
        @param str: color - The color to draw the text in
    """
    drawing = ImageDraw.Draw(image)
    letter_spacing = image.size[0] / len(line)
    x, y = pos

    for char in line:
        drawing.text((x, y), char, fill=ImageColor.getrgb(color), font=font)
        x += letter_spacing

def get_table_rows(json_dict, title, format_len=0):
    """ Extracts each json row into a list of formatted strings
        @param dict: json_dict - The json dict to turn into a table
        @param str: title - the header for the table
        @param int: format_len - How much string format spacing to add
    """
    rows = []
    longest_row = ""

    for key in json_dict:
        left = str(key) + " : "
        right = str(json_dict[key])

        text = f"{left:<{format_len}s} {right:<{format_len}s}"
        longest_row = text if len(text) > len(longest_row) else longest_row

        rows.append(text)

    return [title, "-" * len(longest_row)] + rows

def json_2_table_png(json, table_title, x_pad=0, y_pad=0, format_len=0, txt_color = "black", bg_color="white", fontsize=20, output_path="./json_image.png"):
    """ Takes a json string, draws it as a table on an image, and saves it to a png.
        @param str: json - the json to add to image
    """
    json_dict = literal_eval(json)
    table_rows = get_table_rows(json_dict, table_title, format_len)
    
    font = ImageFont.truetype("Monaco.dfont", fontsize)
    img_size = get_img_size(table_rows, font, x_pad, y_pad)
    image = Image.new('RGB', img_size, color = ImageColor.getrgb(bg_color))  

    y_start = 0
    y_spacing = ImageDraw.Draw(Image.new('RGB', (0,0))).textsize("A", font=font)[1]

    for row in table_rows:
        print(row)
        write_line_to_image(image, row, font, pos=(0, y_start), color=txt_color)
        y_start += y_spacing
        
    image.save(output_path)
    return output_path



if __name__ == "__main__":
    test_json = '{"TJ" : "01:40:00", "Lauren" : "00:40:00", "Steven" : "00:10:01", "Jake" : "00:07:22", "Tess" : "00:01:01"}'

    output = json_2_table_png(test_json, format_len=10, table_title="Individual Scores", txt_color="white", bg_color="black")
    print("Saved image to", output)