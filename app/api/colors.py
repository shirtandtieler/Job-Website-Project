
def lerp_color(frac: float, from_hex: str, to_hex: str):
    frac = min(1, max(0, frac))
    _from = tuple(int(from_hex.lstrip("#")[i:i+2], 16) for i in (0, 2, 4))
    _to = tuple(int(to_hex.lstrip("#")[i:i+2], 16) for i in (0, 2, 4))
    dr = int(round((_to[0]-_from[0]) * frac + _from[0]))
    dg = int(round((_to[1]-_from[1]) * frac + _from[1]))
    db = int(round((_to[2]-_from[2]) * frac + _from[2]))
    return "#" + "".join(f'{i:02x}' for i in [dr, dg, db])
