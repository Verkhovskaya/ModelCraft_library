import numpy as np
import os
from fpdf import FPDF
from PIL import Image
import shutil
import sys
import copy
import random
import math


def generate_layout_files(destination_path, read_map, settings):
    generate_icon(destination_path, read_map)
    settings['line_locations'] = line_positions(read_map, spacing=10)
    image_path = destination_path + "/layout_images"
    if os.path.exists(image_path):
        shutil.rmtree(image_path)
    os.mkdir(image_path)
    image_cropped_path = destination_path + "/layout_cropped_images"
    if os.path.exists(image_cropped_path):
        shutil.rmtree(image_cropped_path)
    os.mkdir(image_cropped_path)
    level_image_paths = generate_level_images(image_path, read_map, settings)
    generate_level_pdf(destination_path, level_image_paths, settings)


def generate_icon(destination_path, blocks):
    block_colors = {1: (100, 100, 100), 2: (150, 180, 100), 3: (100, 80, 60),  4: (80, 80, 80), 5: (150, 130, 80),
                    6: (130, 100, 50), 7: (30, 30, 30), 8: (40, 60, 240), 9: (40, 60, 240), 10: (180, 60, 30),
                    11: (180, 60, 30), 12: (200, 200, 150), 13: (50, 50, 50), 14: (200, 200, 110), 15: (160, 140, 130),
                    16: (70, 70, 70), 17: (160, 130, 90), 18: (120, 150, 100), 19: (200, 200, 90), 20: (250, 250, 250),
                    21: (50, 70, 150), 22:(20, 30, 60), 23: (70, 70, 70), 24: (200, 200, 150), 25: (100, 170, 50),
                    26: (120, 30, 30), 27: (120, 180, 90), 28: (70, 20, 20), 29: (110, 130, 80), 30:(230, 230, 230),
                    31: (50, 80, 50), 32: (140, 100, 50), 33: (120, 100, 70), 34: (120, 100, 70), 35: (210, 210, 210),
                    36: (0, 0, 0), 37: (240, 250, 80), 38: (200, 40, 30), 39: (190, 150, 120), 40:(230, 70, 60),
                    41: (240, 240, 110), 42: (210, 210, 210), 43: (150, 150, 150), 44: (155, 155, 155), 45: (125, 80, 60),
                    46: (100, 40, 20), 47: (140, 120, 80), 48: (90, 110, 90), 49: (20, 20, 30), 50: (210, 150, 80),
                    51: (180, 100, 40), 52: (40, 50, 50)}
    pixels_per_block = 10
    image = np.zeros((blocks.shape[0]*pixels_per_block, blocks.shape[2]*pixels_per_block, 3), dtype=np.uint8)
    for y in range(blocks.shape[1])[::-1]:
        for x in range(blocks.shape[0]):
            for z in range(blocks.shape[2]):
                if (blocks[x,y,z] != 0) and sum(image[x*pixels_per_block, z*pixels_per_block]) == 0:
                    if isinstance(blocks[x,y,z], np.bool_):
                        if y > 0:
                            image[x * pixels_per_block:(x + 1) * pixels_per_block,
                            z * pixels_per_block:(z + 1) * pixels_per_block] = [int(255*y/blocks.shape[1]) for iter_val in range(3)]
                        else:
                            image[x * pixels_per_block:(x + 1) * pixels_per_block,
                            z * pixels_per_block:(z + 1) * pixels_per_block] = [255, 255, 255]
                    else:
                        image[x * pixels_per_block:(x + 1) * pixels_per_block,
                        z * pixels_per_block:(z + 1) * pixels_per_block] = block_colors.get(int(blocks[x,y,z]), (100,0,0))
    img = Image.fromarray(image, 'RGB')
    img_name = destination_path + "/icon.png"
    img.save(img_name)


def generate_level_images(image_path, read_map, settings):
    image_names = []
    y_size = read_map.shape[1]
    for y in range(1,y_size):
        data = draw_level(20, read_map, y, settings)
        data = np.rot90(data, k=1, axes=(0, 1))
        img = Image.fromarray(data, 'RGB')
        img_name = image_path + "/" + str(y) + ".png"
        image_names.append(img_name)
        img.save(img_name)
    return image_names


def draw_level(pixel_size, read_map, y, settings):
    colors = {0: [255, 255, 255], 1: [0,0,0], 2: [0,0,255], 3: [255, 0, 0], 4: [100, 100, 100]}

    color_array = np.zeros((read_map.shape[0], read_map.shape[2]))
    color_array += read_map[:,y,:]

    image = np.zeros((read_map.shape[0] * pixel_size, read_map.shape[2] * pixel_size, 3), dtype=np.uint8) + 100
    for x in range(color_array.shape[0]):
        # 2D color array
        for z in range(color_array.shape[1]):
            image[z * pixel_size:(z + 1) * pixel_size, x * pixel_size:(x + 1) * pixel_size] = colors.get(int(color_array[x, z]), [50, 50, 50])

    sections_x = settings['line_locations'][1]
    sections_z = settings['line_locations'][0]
    for x in sections_x:
        image[max(0,x * pixel_size-2): x*pixel_size+3,:] = [255,0,0]
    for z in sections_z:
        image[:,max(0,z * pixel_size-2): z*pixel_size+3] = [255,0,0]

    for x in range(color_array.shape[1]):
        image[x * pixel_size-1: x*pixel_size+2,:] = [100,100,100]
    for z in range(color_array.shape[0]):
        image[:,z * pixel_size-1: z*pixel_size+2] = [100,100,100]

    return image


def line_positions(block_array, spacing=10):
    array_x = block_array.shape[0]
    array_z = block_array.shape[2]
    x_cuts = [0] + [i*spacing for i in range(1, int(array_x/spacing))]
    z_cuts = [0] + [i*spacing for i in range(1, int(array_z/spacing))]

    x_cuts.append(array_x)
    z_cuts.append(array_z)
    return x_cuts, z_cuts




def generate_level_pdf(destination_path, image_paths, settings):
    section_locations = settings['line_locations']
    side_length = float(settings['thickness'])

    page_width = 207  # units
    page_height = 289  # units
    page_margin = 0
    mm = page_width/(8*25.4)  # units
    array_x = settings['size_x']*mm*side_length
    array_y = settings['size_z']*mm*side_length
    text_y = 10

    pdf = FPDF()
    pdf.set_text_color(50,50,50)
    pdf.add_page()
    pdf.set_font('Times', 'B', 40)
    pdf.text(page_width/2-37, int(page_height*.2), "ModelCraft")
    pdf.set_font('Times', 'B', 30)
    pdf.text(page_width/2-30, int(page_height*.2+15), "Custom map")
    pdf.set_font('Times', 'B', 20)
    pdf.text(page_width/2-50, int(page_height*.2+25), "Created at: " + settings["timestamp"])

    pdf.image(destination_path + "/icon.png", page_width*0.1, page_height*0.4, page_width*0.8, page_height*0.4)



    img_x = settings['size_x'] * side_length
    img_z = settings['size_z'] * side_length

    if img_x < page_width-page_margin*2 and img_z < page_height-page_margin*2:  # 8x11 inches
        while image_paths:
            pdf.add_page()
            num_across = min(1, int((page_width-page_margin*2) / img_x))
            num_down = min(1, int((page_height-page_margin*2) / (img_z)))
            x_offset = 0
            z_offset = 0
            if num_across > 1:
                spacing_x = (page_width-page_margin*2 - num_across * img_x) / (num_across-1)
            else:
                spacing_x = 0
                x_offset = (page_width - img_x)/2
            if num_down > 1:
                spacing_z = (page_height-page_margin*2 - num_down*(text_z+img_z)) / (num_down-1)
            else:
                spacing_z = 0
                z_offset = (page_height - img_z)/2

            for z in range(num_down):
                for x in range(num_across):
                    if image_paths:
                        image = image_paths.pop(0)
                        level = str(int(image.split("/")[-1][:-4])+1)
                        pdf.text(page_margin+x*spacing_x + x*img_x+x_offset, page_margin+z*spacing_z-text_z+7+z_offset + z*(img_z+text_z), "Level " + level)
                        pdf.image(image, page_margin+x*spacing_x + x*img_x + x_offset, page_margin+z*spacing_z + z*(img_z+text_z) + z_offset, array_x, array_z)

    else:
        for i in range(len(image_paths)):
            image_path = image_paths[i]
            section_size_x_units = section_locations[0][1]*20
            section_size_y_units = section_locations[1][1]*20
            section_size_x_pdf = section_size_x_units*mm/20*side_length
            section_size_y_pdf = section_size_y_units*mm/20*side_length
            num_sections_across = len(section_locations[0])-1
            num_sections_down = len(section_locations[1])-1
            sections_across = int((page_width-2.0*page_margin)/section_size_x_pdf)
            sections_down = int((page_height-2.0*page_margin)/section_size_y_pdf)
            pages_across = int(math.ceil((len(section_locations[0])-1.0)/sections_across))
            pages_down = int(math.ceil((len(section_locations[1])-1.0)/sections_down))
            for page_across in range(pages_across):
                for page_down in range(pages_down):
                    pdf.add_page()
                    original = Image.open(image_path)

                    section_start_x = page_across*sections_across + 1
                    section_start_y = page_down*sections_down + 1
                    section_end_x = min(num_sections_across, (page_across+1)*sections_across)
                    section_end_y = min(num_sections_down, (page_down+1)*sections_down)

                    left = (section_start_x-1)*section_size_x_units
                    top = (section_start_y-1)*section_size_y_units
                    right = section_end_x*section_size_x_units
                    bottom = section_end_y*section_size_y_units
                    cropped_image = original.crop((left, top, right, bottom))
                    z = image_path.split("/")[-1][:-4]
                    cropped_path = destination_path + "/layout_cropped_images/" +  z + "_" + str(page_across) + "_" + str(page_down) + ".png"
                    cropped_image.save(cropped_path)

                    pdf_size_x = cropped_image.size[0]/20*mm*side_length
                    pdf_size_y = cropped_image.size[1]/20*mm*side_length

                    pdf_start_x = (page_width-pdf_size_x)/2
                    pdf_start_y = (page_height-pdf_size_y)/2

                    pdf.image(cropped_path, pdf_start_x, pdf_start_y, pdf_size_x, pdf_size_y)
                    pdf.text(page_width/2-40, 20, "Level " + str(i+1) + " / " + str(len(image_paths)))
                    pdf.text(page_width/2-40, 30, "Across: sections " +
                             str(section_start_x) + " - " + str(section_end_x) + " / " + str(num_sections_across))
                    pdf.text(page_width/2-40, 40, "Down: sections " +
                             str(section_start_y) + " - " + str(section_end_y) + " / " + str(num_sections_down))

    pdf.output(destination_path + "/layout.pdf", "F")


