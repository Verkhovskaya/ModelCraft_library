import numpy as np
import os
from PIL import Image

def generate_layout_images(raw_map, args, colors):
    os.mkdir(args.out + "/img")
    for y in range(1,raw_map.shape[1]):
        level = raw_map[:,y,:]
        image = np.zeros((level.shape[0] * args.pixels + args.line_width, level.shape[1] * args.pixels + args.line_width, 3), dtype=np.uint8)
        for x in range(level.shape[0]):
            for z in range(level.shape[1]):
                image[x * args.pixels:(x + 1) * args.pixels, z * args.pixels:(z + 1) * args.pixels, ] = colors[level[x, z]]

        for x in range(level.shape[1]):
            image[x * args.pixels: x*args.pixels+args.line_width,:] = args.line_color
        for z in range(level.shape[0]):
            image[:,z * args.pixels: z*args.pixels+args.line_width] = args.line_color
        image[:,-args.line_width:] = args.line_color
        image[-args.line_width:,:] = args.line_color
        img_name = args.out + "/img/" + str(y) + ".png"
        Image.fromarray(image, 'RGB').save(img_name)

