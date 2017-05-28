M = 0.514307653
C = -23.26893739

def channel_to_energy_kev(c):
    return M*c + C


def energy_kev_to_channel(e):
    return round((e - C) / M)

