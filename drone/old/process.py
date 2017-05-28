def find_bounds(events):
    min_x, max_x = 0, 0
    min_y, max_y = 0, 0
    min_z, max_z = 0, 0

    for event in events:
        x, y, z = event.fields['world_position']

        if x < min_x:
            min_x = x

        elif x > max_x:
            max_x = x

        if y < min_y:
            min_y = y

        elif y > max_y:
            max_y = y

        if z < min_z:
            min_z = z

        elif z > max_z:
            max_z = z

    return dict(min_x=min_x, max_x=max_x, min_y=min_y, max_y=max_y)

def bin_events(events, bounds, cell_dimensions):
    """Group together all events into n^3 bins"""
    min_x = bounds['min_x']
    min_y = bounds['min_y']
    min_z = bounds['min_z']

    for event in events:
        world = event.fields['world_position']

        x_bin = int(world.x // cell_dimensions.x)
        y_bin = int(world.y // cell_dimensions.y)
        z_bin = int(world.z // cell_dimensions.z)

        event.fields['bin'] = x_bin, y_bin, z_bin
