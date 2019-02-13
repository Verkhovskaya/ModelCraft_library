import read_minecraft_map
import read_voxel_file
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
    'material_length': 1000,
    'material_width': 1000,
    'max_cutout_piece_size': 50,
    'tab_size': 0.3,
}

read_map = read_voxel_file.read_voxel_file('/Users/2017-A/Dropbox/python_libraries/ModelCraft_library/test_data/day1_fyord.vox');
# read_map = read_map.read_map(map_path, start, end)
generate_layout_files.generate_layout_files(destination_path, read_map, settings)
generate_cutout_files.generate_laser_cut_files(destination_path, read_map, settings)
print("Done!")