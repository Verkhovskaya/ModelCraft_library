import read_map
import generate_layout_files
import generate_cutout_files
import numpy as np

start = np.array([311,2,245])
end = np.array([331,6,265])
map_path = '/Users/2017-A/Dropbox/python_libraries/ModelCraft_library/test_data/20by20'
destination_path = '/Users/2017-A/Dropbox/python_libraries/ModelCraft_library/generated'
settings = {
    'thickness': 3,
    'size_x': 100,
    'size_z': 100,
    'timestamp': 'TODAY',
    'material_length': 100,
    'material_width': 100,
    'max_cutout_piece_size': 100,
    'tab_size': 0.3,
}

read_map = read_map.read_map(map_path, start, end)
print(read_map)
generate_layout_files.generate_layout_files(destination_path, read_map, settings)
generate_cutout_files.generate_laser_cut_files(destination_path, read_map, settings)
print("HELLO")