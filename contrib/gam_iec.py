import gam
import gam_g4 as g4
from anytree import LevelOrderIter
import numpy as np

iec_plastic = 'IEC_PLASTIC'
water = 'G4_WATER'
iec_lung = 'G4_LUNG_ICRP'


def create_material():
    n = g4.G4NistManager.Instance()
    elems = ['C', 'H', 'O']
    nbAtoms = [5, 8, 2]
    gcm3 = gam.g4_units('g/cm3')
    n.ConstructNewMaterial('IEC_PLASTIC', elems, nbAtoms, 1.18 * gcm3)


def add_phantom(simulation, name='iec'):
    # unit
    cm = gam.g4_units('cm')
    mm = gam.g4_units('mm')
    deg = gam.g4_units('deg')
    create_material()

    # colors
    red = [1, 0.7, 0.7, 0.8]
    blue = [0.5, 0.5, 1, 0.8]
    gray = [0.5, 0.5, 0.5, 1]

    # check overlap
    simulation.g4_check_overlap_flag = True

    # top 
    top_shell = simulation.new_solid('Tubs', f'{name}_top_shell')
    top_shell.RMax = 15 * cm
    top_shell.RMin = 0
    top_shell.Dz = 21.4 * cm / 2
    top_shell.SPhi = 0 * deg
    top_shell.DPhi = 180 * deg

    # Lower left half of phantom
    bottom_left_shell = simulation.new_solid('Tubs', f'{name}_bottom_left_shell')
    bottom_left_shell.RMax = 8 * cm
    bottom_left_shell.RMin = 0
    bottom_left_shell.Dz = 21.4 * cm / 2
    bottom_left_shell.SPhi = 270 * deg
    bottom_left_shell.DPhi = 90 * deg

    # Lower right half of phantom
    bottom_right_shell = simulation.new_solid('Tubs', f'{name}_bottom_right_shell')
    gam.vol_copy(bottom_left_shell, bottom_right_shell)
    bottom_right_shell.SPhi = 180 * deg

    # Bottom box
    bottom_central_shell = simulation.new_solid('Box', f'{name}_bottom_central_shell')
    bottom_central_shell.size = [14 * cm, 8 * cm, 21.4 * cm]

    c = -bottom_central_shell.size[1] / 2

    # union
    shell = gam.solid_union(top_shell, bottom_left_shell, [7 * cm, 0, 0])
    shell = gam.solid_union(shell, bottom_central_shell, [0, c, 0])
    shell = gam.solid_union(shell, bottom_right_shell, [-7 * cm, 0, 0])
    iec = simulation.add_volume_from_solid(shell, name)
    iec.material = iec_plastic
    iec.color = red

    # Inside space for the water, same than the shell, with 0.3cm less
    thickness = 0.3 * cm
    top_interior = simulation.new_solid('Tubs', f'{name}_top_interior')
    gam.vol_copy(top_shell, top_interior)
    top_interior.RMax -= thickness
    top_interior.Dz -= thickness
    bottom_left_interior = simulation.new_solid('Tubs', f'{name}_bottom_left_interior')
    gam.vol_copy(bottom_left_shell, bottom_left_interior)
    bottom_left_interior.RMax -= thickness
    bottom_left_interior.Dz -= thickness
    bottom_right_interior = simulation.new_solid('Tubs', f'{name}_bottom_right_interior')
    gam.vol_copy(bottom_left_interior, bottom_right_interior)
    bottom_right_interior.SPhi = 180 * deg
    bottom_central_interior = simulation.new_solid('Box', f'{name}_bottom_central_interior')
    gam.vol_copy(bottom_central_shell, bottom_central_interior)
    bottom_central_interior.size[1] -= thickness
    bottom_central_interior.size[2] -= thickness

    # union
    interior = gam.solid_union(top_interior, bottom_left_interior, [7 * cm, 0, 0])
    interior = gam.solid_union(interior, bottom_central_interior, [0, c + thickness / 2, 0])
    interior = gam.solid_union(interior, bottom_right_interior, [-7 * cm, 0, 0])
    interior = simulation.add_volume_from_solid(interior, f'{name}_interior')
    interior.mother = name
    interior.material = water
    interior.color = blue

    # central tube in iec_plastic
    cc = simulation.add_volume('Tubs', f'{name}_center_cylinder')
    cc.mother = f'{name}_interior'
    cc.RMax = 2.5 * cm
    cc.RMin = 2.1 * cm
    cc.Dz = top_interior.Dz
    cc.SPhi = 0 * deg
    cc.DPhi = 360 * deg
    cc.material = iec_plastic
    cc.translation = [0, 3.5 * cm, 0]
    cc.color = red

    # central tube lung material
    hscc = simulation.add_volume('Tubs', f'{name}_center_cylinder_hole')
    hscc.mother = f'{name}_interior'
    hscc.RMax = 2.1 * cm
    hscc.RMin = 0 * cm
    hscc.Dz = top_interior.Dz
    hscc.material = iec_lung
    hscc.translation = [0, 3.5 * cm, 0]
    hscc.color = gray

    # spheres
    v = f'{name}_interior'
    iec_add_sphere(simulation, name, v,
                   10 * mm, 1 * mm, 3 * mm, [2.86 * cm, c + 2.39633 * cm, 3.7 * cm])
    iec_add_sphere(simulation, name, v,
                   13 * mm, 1 * mm, 3 * mm, [-2.86 * cm, c + 2.39633 * cm, 3.7 * cm])
    iec_add_sphere(simulation, name, v,
                   17 * mm, 1 * mm, 3 * mm, [-5.72 * cm, 3.5 * cm, 3.7 * cm])
    iec_add_sphere(simulation, name, v,
                   22 * mm, 1 * mm, 3.5 * mm, [-2.86 * cm, 8.45367 * cm, 3.7 * cm])
    iec_add_sphere(simulation, name, v,
                   28 * mm, 1 * mm, 3.5 * mm, [2.86 * cm, 8.45367 * cm, 3.7 * cm])
    iec_add_sphere(simulation, name, v,
                   37 * mm, 1 * mm, 3.5 * mm, [5.72 * cm, 3.5 * cm, 3.7 * cm])

    return iec


def add_phantom_old(simulation, name='iec'):
    cm = gam.g4_units('cm')
    mm = gam.g4_units('mm')
    deg = gam.g4_units('deg')
    create_material()

    # colors
    white = [1, 1, 1, 1]
    red = [1, 0, 0, 1]
    blue = [0, 0, 1, 1]
    lightblue = [0.4, 0.4, 1, 1]
    gray = [0.5, 0.5, 0.5, 1]
    green = [0, 1, 0, 1]

    # material
    simulation.g4_check_overlap_flag = False

    # main volume
    iec = simulation.add_volume('Tubs', 'iec')
    iec.RMax = 17 * cm
    iec.RMin = 0 * cm
    iec.Dz = 22 * cm / 2
    iec.SPhi = 0 * deg
    iec.DPhi = 360 * deg
    iec.material = 'G4_AIR'
    iec.color = white

    # ---------------------
    # Upper Half of Phantom

    # Upper outer shell
    uos = simulation.add_volume('Tubs', 'upper_outer_shell')
    uos.mother = 'iec'
    uos.RMax = 15 * cm
    uos.RMin = 14.7 * cm
    uos.Dz = 21.4 * cm / 2
    uos.SPhi = 0 * deg
    uos.DPhi = 180 * deg
    uos.material = iec_plastic
    uos.translation = [0, -3.5 * cm, 0]

    # Upper interior
    ui = simulation.add_volume('Tubs', 'upper_interior')
    gam.vol_copy(uos, ui)
    ui.RMax = uos.RMin
    ui.RMin = 0 * cm
    ui.material = 'G4_WATER'

    # iec_plastic Shell Surrounding Lung Insert (Center Cylinder)
    cc = simulation.add_volume('Tubs', 'center_cylinder')
    cc.mother = 'upper_interior'
    cc.RMax = 2.5 * cm
    cc.RMin = 2.1 * cm
    cc.Dz = uos.Dz
    cc.SPhi = 0 * deg
    cc.DPhi = 360 * deg
    cc.material = iec_plastic
    cc.translation = [0, 3.5 * cm, 0]

    # Hollow Space in Central Cylinder
    hscc = simulation.add_volume('Tubs', 'center_cylinder_hole')
    hscc.mother = 'upper_interior'
    hscc.RMax = 2.1 * cm
    hscc.RMin = 0 * cm
    hscc.Dz = uos.Dz
    hscc.material = 'G4_LUNG_ICRP'
    hscc.translation = [0, 3.5 * cm, 0]

    # Exterior Shell of Upper Half of Phantom

    # Top Side
    ts = simulation.add_volume('Tubs', 'top_shell')
    ts.mother = 'iec'
    ts.RMax = 15 * cm
    ts.RMin = 0 * cm
    ts.Dz = 0.3 * cm / 2
    ts.SPhi = 0 * deg
    ts.DPhi = 180 * deg
    ts.translation = [0, -3.5 * cm, 10.85 * cm]
    ts.material = iec_plastic

    # bottom side
    bs = simulation.add_volume('Tubs', 'bottom_shell')
    gam.vol_copy(ts, bs)
    bs.translation[2] *= -1

    # Lower left half of phantom
    blos = simulation.add_volume('Tubs', 'bottom_left_outer_shell')
    blos.mother = 'iec'
    blos.RMax = 8 * cm
    blos.RMin = 7.7 * cm
    blos.Dz = 21.4 * cm / 2
    blos.SPhi = 270 * deg
    blos.DPhi = 90 * deg
    blos.translation = [7 * cm, -3.5 * cm, 0]
    blos.material = iec_plastic

    # Lower Left interior
    lli = simulation.add_volume('Tubs', 'lower_left_interior')
    gam.vol_copy(blos, lli)
    lli.RMax = blos.RMin
    lli.RMin = 0
    lli.material = 'G4_WATER'

    # Lower right half of phantom
    bros = simulation.add_volume('Tubs', 'bottom_right_outer_shell')
    gam.vol_copy(blos, bros)
    bros.SPhi = 180 * deg
    bros.translation[0] *= -1

    # Lower right interior
    lri = simulation.add_volume('Tubs', 'lower_right_interior')
    gam.vol_copy(lli, lri)
    lri.SPhi = 180 * deg
    lri.translation[0] *= -1

    # Bottom box
    bb = simulation.add_volume('Box', 'bottom_box')
    bb.size = [14 * cm, 0.3 * cm, 21.4 * cm]
    bb.translation = [0, -11.35 * cm, 0]
    bb.mother = 'iec'
    bb.material = iec_plastic

    # Interior box
    ib = simulation.add_volume('Box', 'interior_box')
    gam.vol_copy(bb, ib)
    ib.material = 'G4_WATER'
    ib.size[1] = 7.7 * cm
    ib.translation[1] = -7.35 * cm

    # top shell
    ts2 = simulation.add_volume('Tubs', 'top_shell2')
    ts2.mother = 'iec'
    ts2.RMax = 8 * cm
    ts2.RMin = 0 * cm
    ts2.Dz = 0.3 * cm / 2
    ts2.SPhi = 270 * deg
    ts2.DPhi = 90 * deg
    ts2.material = iec_plastic
    ts2.translation = [7 * cm, -3.5 * cm, 10.85 * cm]

    # top shell
    ts3 = simulation.add_volume('Tubs', 'top_shell3')
    gam.vol_copy(ts2, ts3)
    ts3.SPhi = 180 * deg
    ts3.translation[0] *= -1

    # top shell
    ts4 = simulation.add_volume('Box', 'top_shell4')
    ts4.mother = 'iec'
    ts4.size = [14 * cm, 8 * cm, 0.3 * cm]
    ts4.material = iec_plastic
    ts4.translation = [0 * cm, -7.5 * cm, 10.85 * cm]

    # bottom shell
    bs2 = simulation.add_volume('Tubs', 'bottom_shell2')
    gam.vol_copy(ts2, bs2)
    bs2.translation[2] *= -1

    # bottom shell
    bs3 = simulation.add_volume('Tubs', 'bottom_shell3')
    gam.vol_copy(ts3, bs3)
    bs3.translation[2] *= -1

    # bottom shell
    bs4 = simulation.add_volume('Box', 'bottom_shell4')
    gam.vol_copy(ts4, bs4)
    bs4.translation[2] *= -1

    # spheres
    iec_add_sphere(simulation, name, 'interior_box',
                   10 * mm, 1 * mm, 3 * mm, [2.86 * cm, 2.39633 * cm, 3.7 * cm])
    iec_add_sphere(simulation, name, 'interior_box',
                   13 * mm, 1 * mm, 3 * mm, [-2.86 * cm, 2.39633 * cm, 3.7 * cm])
    iec_add_sphere(simulation, name, 'upper_interior',
                   17 * mm, 1 * mm, 3 * mm, [-5.72 * cm, 3.5 * cm, 3.7 * cm])
    iec_add_sphere(simulation, name, 'upper_interior',
                   22 * mm, 1 * mm, 3.5 * mm, [-2.86 * cm, 8.45367 * cm, 3.7 * cm])
    iec_add_sphere(simulation, name, 'upper_interior',
                   28 * mm, 1 * mm, 3.5 * mm, [2.86 * cm, 8.45367 * cm, 3.7 * cm])
    iec_add_sphere(simulation, name, 'upper_interior',
                   37 * mm, 1 * mm, 3.5 * mm, [5.72 * cm, 3.5 * cm, 3.7 * cm])

    # colors
    tree = simulation.volume_manager.build_tree()
    vol = tree[iec.name]
    for v in LevelOrderIter(vol):
        vv = simulation.volume_manager.volumes[v.name].user_info
        if vv.material == water:
            vv.color = blue
        if vv.material == iec_plastic:
            vv.color = lightblue
        if vv.material == iec_lung:
            vv.color = gray
        if 'sphere' in vv.name:
            vv.color = green
        if 'capillary' in vv.name:
            vv.color = green

    ts2.color = [1, 0, 0, 1]

    return iec


def iec_add_sphere(sim, name, vol, diam, sph_thick, cap_thick, position):
    mm = gam.g4_units('mm')
    cm = gam.g4_units('cm')
    d = f'{(diam / mm):.0f}mm'
    rad = diam / 2

    # interior sphere
    sph = sim.add_volume('Sphere', f'{name}_sphere_{d}')
    sph.mother = vol
    sph.translation = position
    sph.Rmax = rad
    sph.Rmin = 0
    sph.material = 'G4_WATER'

    # outer sphere shell
    sphs = sim.add_volume('Sphere', f'{name}_sphere_shell_{d}')
    sphs.mother = vol
    sphs.translation = position
    sphs.Rmax = rad + sph_thick
    sphs.Rmin = rad
    sphs.material = iec_plastic

    # capillary
    cap = sim.add_volume('Tubs', f'{name}_capillary_{d}')
    cap.mother = vol
    cap.translation = position
    cap.material = 'G4_WATER'
    cap.RMax = 0.25 * cm
    cap.RMin = 0 * cm
    # 21.4/2 = 10.7 interior height (top_interior)
    thickness = 0.3 * cm
    h = 21.4 / 2 * cm - thickness
    cap.Dz = (h - 3.7 * cm - rad - sph_thick) / 2.0
    cap.translation[2] = 3.7 * cm + rad + sph_thick + cap.Dz

    # capillary outer shell
    caps = sim.add_volume('Tubs', f'{name}_capillary_shell_{d}')
    gam.vol_copy(cap, caps)
    caps.material = iec_plastic
    caps.RMax = cap_thick
    caps.RMin = cap.RMax


def add_sources(simulation, name, spheres, activity_concentrations):
    spheres_diam = [10, 13, 17, 22, 28, 37]
    sources = []
    if spheres == 'all':
        spheres = spheres_diam
    for sphere, ac in zip(spheres, activity_concentrations):
        if sphere in spheres_diam:
            s = add_source(simulation, name, float(sphere), float(ac))
            sources.append(s)
    return sources


def add_source(simulation, name, diameter, ac):
    MeV = gam.g4_units('MeV')
    Bq = gam.g4_units('Bq')
    mm = gam.g4_units('mm')
    d = f'{(diameter / mm):.0f}mm'
    volume = np.pi * np.power(diameter / 2, 2)
    print('volume', volume)
    source = simulation.add_source('Generic', f'{name}_{d}')
    source.particle = 'e-'
    source.energy.mono = 0.05 * MeV  ## todo fluor !
    source.direction.type = 'iso'
    source.activity = ac * volume * Bq
    print('axtivity', source.activity)
    source.position.type = 'sphere'
    source.position.radius = diameter / 2 * mm
    print('radius', source.position.radius/mm)
    source.position.center = [0, 0, 0]
    source.mother = f'{name}_sphere_{d}'
    print(source)
    return source
