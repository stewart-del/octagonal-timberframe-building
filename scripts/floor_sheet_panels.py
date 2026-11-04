# TIMESTAMP START 2026-11-04T23:17:24+00:00 | REVISION R000029
"""Cut the occupied underlayment into staggered 4 × 8-foot stock cells."""
import math
import numpy as np
import manifold3d as m

INCH = .0254
NORTH = np.array([math.cos(math.pi/8), 0., -math.sin(math.pi/8)])
EAST = np.array([-NORTH[2], 0., NORTH[0]])
LENGTH = 96*INCH
WIDTH = 48*INCH

def cut_sheets(solid):
    """No kerf gaps: preserve the complete occupied floor and existing notches."""
    vertices = np.asarray(solid.to_mesh64().vert_properties)[:, :3]
    emin, emax = (vertices@EAST).min(), (vertices@EAST).max()
    nmin, nmax = (vertices@NORTH).min(), (vertices@NORTH).max()
    sheets = []
    for row in range(math.floor(nmin/WIDTH-.5), math.ceil(nmax/WIDTH-.5)):
        v0 = (row+.5)*WIDTH
        stagger = ((row+1) % 2)*LENGTH/2
        for column in range(math.floor((emin-stagger)/LENGTH), math.ceil((emax-stagger)/LENGTH)):
            u0 = column*LENGTH+stagger
            shape = solid.trim_by_plane(EAST, u0).trim_by_plane(-EAST, -u0-LENGTH)
            shape = shape.trim_by_plane(NORTH, v0).trim_by_plane(-NORTH, -v0-WIDTH)
            if shape.volume() <= 1e-10:
                continue
            assert len(shape.decompose()) == 1, (row, column, 'Disconnected sheet cut')
            stock = {'lengthM': LENGTH, 'widthM': WIDTH, 'thicknessM': .0381,
                     'row': row, 'column': column, 'eastBoundsM': [u0, u0+LENGTH],
                     'northBoundsM': [v0, v0+WIDTH], 'longAxisM': EAST.tolist(),
                     'shortAxisM': NORTH.tolist(), 'staggerM': LENGTH/2,
                     'description': 'Cut from 4 × 8-foot sheet stock; retained 1½-inch display thickness'}
            sheets.append((f'FLOOR-SUBFLOOR-{len(sheets)+1:02d}', shape, stock))
    return sheets

def sheet_metadata(identifier, stock):
    return {'name': f'Underlayment {identifier.rsplit("-", 1)[1]} · cut 4 × 8 ft sheet',
            'floorRole': 'underlayment_sheet', 'sheet_stock': stock,
            'stock_frame': {'axis': EAST.tolist(), 'width': NORTH.tolist(), 'depth': [0, 1, 0]},
            'fabrication_dimensions_valid': True}
# TIMESTAMP END 2026-11-04T23:17:24+00:00 | REVISION R000029
