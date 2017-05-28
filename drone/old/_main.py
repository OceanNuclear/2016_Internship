# from argparse import ArgumentParser
# from urllib.request import urlretrieve
# from collections import namedtuple
# from controls import CameraController
# from coordinates import TileCoord, LatLong, CoordinateSystem
# from event import parse_files, FIELD_KEYS
# from shader import create_depth_texture, create_density_texture, create_volume, setup_shader, density_texture_from_array
# from math import ceil
#
# from numpy import empty, uint8, float_, amax, zeros
# from itertools import product
# from os.path import join as join_path, abspath, exists
# from PIL import Image
#
# from panda3d.core import Vec4, Vec3, Mat4F, CardMaker, BitMask32, loadPrcFileData, \
#     NodePath
# from direct.showbase.ShowBase import ShowBase, Filename
# # from direct.showbase.DirectObject import DirectObject
#
# loadPrcFileData("", "win-size 1600 900")
# loadPrcFileData("", "win-origin 10 20")
#
# MapInfo = namedtuple("Map", "coordinate_system tile_indices filepath")
#
# TILE_NAME = "tile_z{z}_x{x}_y{y}.png"
# MAP_NAME = "map_{min_x}_{max_x}_{min_y}_{max_y}.png"
# CACHE_PATH = "cache"
#
# MAPS_URL = 'http://mt2.google.com/vt/lyrs=s&x={x}&y={y}&z={z}&scale={scale}'
#
#
# """This pipeline converts latlong + alt to google maps world coordinate (x, y) and a relative {0 <= z <= 1} Z.
# The xy coordinate is then converted into relative as for z, to give a 3d XYZ texture coordinate, assuming a volume
# domain cube whose dimensions in the XY plane correspond to the map tile, and whose dimensions are equal
#
# """
#
#
# def get_map_bounds(tile_indices):
#     """Find the min and max tile coordinates that define the bounding box for
#     the given tile indices
#     """
#     x_co = [p.x for p in tile_indices]
#     y_co = [p.y for p in tile_indices]
#
#     min_x, *_, max_x = sorted(x_co)
#     min_y, *_, max_y = sorted(y_co)
#
#     return TileCoord(min_x, min_y), TileCoord(max_x, max_y)
#
#
# def get_map_dimensions(map_info):
#     tile_min, tile_max = get_map_bounds(map_info.tile_indices)
#     map_min = map_info.coordinate_system.tile_to_map(min_tile)
#
#     tile_max_bound = TileCoord(max_tile.x+1, max_tile.y+1)
#     map_max = map_info.coordinate_system.tile_to_map(tile_max_bound)
#
#     lat_long_min = map_info.coordinate_system.map_to_lat_long(map_min)
#     lat_long_max = map_info.coordinate_system.map_to_lat_long(map_max)
#
#     x0 = lat_long_min
#     x1 = LatLong(lat_long_min.lat, lat_long_max.long)
#
#     y0 = lat_long_min
#     y1 = LatLong(lat_long_max.lat, lat_long_min.long)
#
#     dx = x1.haversine_dist(x0)
#     dy = y1.haversine_dist(y0)
#
#     return dx, dy
#
#     # TODO find scales, divide by cell dims to get XYZ
#
#
# def create_image_from_tiles(coordinate_system, tile_indices):
#     (min_x, min_y), (max_x, max_y) = get_map_bounds(tile_indices)
#
#     map_name = MAP_NAME.format(min_x=min_x, max_x=max_x, min_y=min_y, max_y=max_y)
#     map_path = abspath(join_path(CACHE_PATH, map_name))
#
#
#     if not exists(map_path):
#         x_range = max_x - min_x + 1
#         y_range = max_y - min_y + 1
#
#         width = x_range * coordinate_system.tile_size
#         height = y_range * coordinate_system.tile_size
#
#         image = Image.new("RGB", (width, height))
#
#         for x, y in product(range(x_range), range(y_range)):
#             tile_x = min_x + x
#             tile_y = min_y + y
#
#             tile_name = TILE_NAME.format(z=coordinate_system.zoom,
#                                          x=tile_x, y=tile_y)
#             tile_path = abspath(join_path(CACHE_PATH, tile_name))
#
#             if not exists(tile_path):
#                 tile_url = MAPS_URL.format(x=tile_x, y=tile_y,
#                                            z=coordinate_system.zoom, scale=1)
#                 request = urlretrieve(tile_url, tile_path)
#
#             tile_image = Image.open(tile_path)
#             tile_coordinates = (x * coordinate_system.tile_size,
#                                 y * coordinate_system.tile_size)
#
#             image.paste(tile_image, tile_coordinates)
#
#         image.save(map_path)
#
#     return MapInfo(coordinate_system, tile_indices, map_path)
#
#
# def map_to_world(point, map_info, card):
#     """Convert google-maps world-space coordinate [map] to panda world space"""
#     min_tile, max_tile = get_map_bounds(map_info.tile_indices)
#     max_tile_bound = TileCoord(max_tile.x+1, max_tile.y+1)
#
#     map_min = map_info.coordinate_system.tile_to_map(min_tile)
#     map_max = map_info.coordinate_system.tile_to_map(max_tile_bound)
#
#     vec = Vec3((point.x-map_min.x)/(map_max.x-map_min.x),
#                 0,
#                (map_max.y-point.y)/(map_max.y-map_min.y))
#     return card.get_mat().xform_point(vec)
#
#
# def map_alt_to_grid_index(map_pos, map_min, map_max, altitude, min_alt, max_alt, data_arr):
#     """Convert from map coords to 3D grid coords"""
#     rel_x = (map_pos.x-map_min.x)/(map_max.x-map_min.x)
#     rel_y = (map_max.y-map_pos.y)/(map_max.y-map_min.y)
#     rel_z = (altitude - min_alt) / (max_alt - min_alt)
#     assert rel_z >= 0 and rel_z <= 1
#     return (round(rel_x * (data_arr.shape[0]-1)),
#             round(rel_y * (data_arr.shape[1]-1)),
#             round(rel_z * (data_arr.shape[2]-1)))
#
#
# def create_map(map_info):
#     texture = loader.loadTexture(Filename.from_os_specific(map_info.filepath))
#
#     # Make map card
#     card_maker = CardMaker('card')
#     card = render.attach_new_node(card_maker.generate())
#     card.set_texture(texture)
#     card.set_hpr(0, -90, 0)
#     card.set_scale(2)
#
#     sx, sy, sz = card.get_scale()
#     card.set_pos(-sx/2, -sy/2, 0)
#     return card
#
#
# def data_pos_to_world(data_pos, volume, axis_bins):
#     ix, iy, iz = data_pos
#     sx, sy, sz = axis_bins
#     fx, fy, fz = (ix+0.5) / (sx - 1), (iy+0.5) / (sy - 1), (iz+0.5)/ (sz - 1)
#     rel = Vec3(fx, fy, fz)
#     vec = rel * 2 - Vec3(1, 1, 1)
#     world = volume.get_mat().xform_point(vec)
#     return world
#
#
# RED = Vec4(1, 0, 0, 1)
# BLUE = Vec4(0, 0, 1, 1)
# GREEN = Vec4(0, 1, 0, 1)
#
# # TODO
# # Currently the data_array isn't carried along all the voxels it contributes to ... for now just take the voxels till next point, later need more data_array! (integrate velocity or something)
# #
#
#
# if __name__ == "__main__":
#     parser = ArgumentParser(description="Volumetric data_array visualiser")
#     parser.add_argument("pattern", type=str, help="Event file pattern (e.g 'events/event*.txt')")
#     parser.add_argument("cell_size", type=float, help="Cell size (x, y, z bin size)")
#     args = parser.parse_args()
#
#     base = ShowBase()
#
#     # Starting coordinate system
#     coordinate_system = CoordinateSystem(zoom=19)
#
#     # Load events and sort by time
#     print("Loading events from disk...")
#     events = [e for e in parse_files(args.pattern) if all(n in e.fields for n in FIELD_KEYS)] # Requires all meta info
#
#     # Add coordinates (map pos)
#     print("Determining map-space positions for events...")
#     for event in events:
#         latitude = event.fields['latitude']['value']
#         longitude = event.fields['longitude']['value']
#
#         # Get XY map position
#         lat_long = LatLong(latitude, longitude)
#         event.fields['map_position'] = map_pos = coordinate_system.lat_long_to_map(lat_long)
#
#     # Create map info
#     print("Finding tile positions for events...")
#     tile_indices = [coordinate_system.map_to_tile(e.fields['map_position']) for e in events]
#
#     print("Loading Google map tiles for region of interest...")
#     map_info = create_image_from_tiles(coordinate_system, tile_indices)
#
#     # Get min and max altitudes
#     min_alt, *_, max_alt = sorted([e.fields['altitude']['value'] for e in events])
#     altitude_range = max_alt, min_alt
#
#     # Get map boundsZZz
#     min_tile, max_tile = get_map_bounds(map_info.tile_indices)
#     max_tile_bound = TileCoord(max_tile.x+1, max_tile.y+1)
#
#     # Find bins in each axis
#     cell_size = args.cell_size
#     cell_dimensions = Vec3(cell_size, cell_size, cell_size)
#     map_dimensions = Vec3(*get_map_dimensions(map_info), (max_alt - min_alt))
#     axis_bins = [ceil(di / ci) for di, ci in zip(map_dimensions, cell_dimensions)]
#
#     print(axis_bins)
#
#     # Populate data_array arr
#     data_arr = zeros(axis_bins, float_)
#
#     map_min = map_info.coordinate_system.tile_to_map(min_tile)
#     map_max = map_info.coordinate_system.tile_to_map(max_tile_bound)
#
#     print("Writing events to {} bins...".format(axis_bins[0] * axis_bins[1] * axis_bins[2]))
#     co_counts = {}
#     for event in events:
#         map_pos = event.fields['map_position']
#         alt = event.fields['altitude']['value']
#
#         data_co = map_alt_to_grid_index(map_pos, map_min, map_max, alt, min_alt, max_alt, data_arr)
#         data_arr[data_co] += sum(event.spectrum)
#         event.fields['data_co'] = data_co
#         co_counts[data_co] = co_counts.get(data_co,0) + 1
#
#     # Take mean of all contributions
#     print("Averaging accumulated bin values...")
#     for coord, n_points in co_counts.items():
#         data_arr[coord] /= n_points
#
#     max_value = amax(data_arr)
#
#     # Create volume array
#     print("Writing data_array to RGBA volume...")
#     volume_arr = empty((*axis_bins, 4), uint8)
#     has_data_array = 0.4
#
#
#     BLUE_TO_RED = RED - BLUE
#     for coord in product(*[range(n) for n in axis_bins]):
#         value = data_arr[coord]
#
#         if not coord in co_counts:
#             continue
#
#         r, g, b, _ = BLUE + BLUE_TO_RED * (value / max_value)
#         volume_arr[coord] = [round(x*255) for x in (b, g, r, has_data_array)]
#
#     from math import isnan
#
#     timestamp_positions = [(e.fields['gps_timestamp']['value'], e.fields['data_co']) for e in events if not isnan(e.fields['gps_timestamp']['value'])]
#     from operator import itemgetter
#     timestamp_positions.sort(key=itemgetter(0))
#
#     from itertools import islice
#
#     print("Loading stupidly large drone model")
#     mod = loader.loadModel("models/drone")
#     mod.reparent_to(render)
#     mod.set_scale(0.15)
#
#     t0 = timestamp_positions[0][0]
#     def task(tsk, data_array={'last_index':0}):
#         speed = 2
#         last_index = data_array['last_index']
#         curr_time = t0 + tsk.time * speed
#         for i in range(last_index, len(timestamp_positions)):
#             t, p = timestamp_positions[i]
#             if t > curr_time:
#                 break
#
#         else:
#             return tsk.cont
#
#         data_array['last_index'] = i
#
#         if i == 0:
#             return tsk.cont
#
#         t1, pos1 = timestamp_positions[i-1]#
#         t2, pos2 = timestamp_positions[i]
#
#         p1 = data_pos_to_world(pos1, volume, axis_bins)
#         p2 = data_pos_to_world(pos2, volume, axis_bins)
#         fac = (curr_time - t1) / (t2 - t1)
#
#         p = p1 + (p2 - p1) * fac
#         mod.set_pos(p)
#
#
#         return tsk.cont
#
#     taskMgr.add(task, "T")
#
#
#     # Origin at 0, 0, 0
#     map_nodepath = create_map(map_info)
#
#     # Don't render the volume cube to the depth texture, so have the depth cam ignore the mask
#     camera_render_mask = BitMask32(4)
#     depth = create_depth_texture(camera_render_mask)
#
#     # Volume is 2x2x2, with mask of camera_render_mask (ignored by depth tex cam)
#     volume = create_volume(camera_render_mask)
#
#     # Assume X & Y dimensions are ~ equal
#     z_scale = map_dimensions.z / map_dimensions.x
#     volume.set_scale(1, 1, z_scale)
#     volume.set_pos(0, 0, 0.5)
#
#     # tex = create_density_texture()
#     tex = density_texture_from_array(volume_arr)
#     setup_shader(volume, tex, depth, (1,0,0))
#
#     # Camera controller (LEFT, RIGHT, UP, DOWN)
#     controller = CameraController(base.cam, height=2, radius=5)
#
#     # TODO  Slice planes
#
#
#     base.run()


from panda3d.core import Mat4, Vec3


pts = [Vec3(0, 0, i) for i in range(5)]
trans = Mat4.translate_mat(50, 0, 0)
rot_lat = Mat4.rotate_mat(lat, )