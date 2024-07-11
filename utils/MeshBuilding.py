import bpy
from scipy.interpolate import splprep, splev
import pyvista as pv
import numpy as np
import os

# Building dura and cord mesh (closed)
def getMeshSplines(loops, type):
    """
    Create closed mesh splines based on the provided loops.

    Parameters
    ----------
    loops : list of lists
        List containing loops of coordinates for dura or cord creation
    type : string
        Type of mesh (e.g., 'dura', 'cord')

    Returns
    -------
    None
    """
    # Select collection to add objects
    collection_name = "Collection"
    selected_collection = bpy.context.scene.collection.children.get(collection_name)
    
    # Iterate over loops
    for i in range(len(loops)):
        # Create an empty Curve object
        curve = bpy.data.curves.new(name=f"{type}_Loop{i}", type='CURVE')
        curve.dimensions = '3D'
        
        # Create a Curve object from the empty one
        obj = bpy.data.objects.new(f"{type}_loop{i}", curve)
        
        # Add the created object to the current collection
        if selected_collection:
            selected_collection.objects.link(obj)
        else:
            print(f"Collection '{collection_name}' not found.")
        
        # Set Curve object to spline type
        spline = curve.splines.new(type='NURBS')
        spline.radius_interpolation = 'CARDINAL'
        spline.tilt_interpolation = 'CARDINAL'
        spline.use_cyclic_u = True
        spline.points.add(len(loops[i]) - 1)
        
        # Set spline points coordinates
        for j, coord in enumerate(loops[i]):
            spline.points[j].co = (coord[0], coord[1], coord[2], 1)
        
        # Convert curve to mesh type
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = bpy.data.objects[f"{type}_loop{i}"]
        bpy.data.objects[f"{type}_loop{i}"].select_set(True)
        bpy.ops.object.convert(target='MESH')
    
    # Update scene
    bpy.context.view_layer.update()
    
    # Join all CURVE MESH objects into one MESH
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.object.select_by_type(type='MESH')
    bpy.ops.object.join()
    
    # Select the merged 'MESH' object
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.object.select_by_type(type='MESH')
    obj = bpy.context.selected_objects[0]
    new_name = f"{type}_Loops"
    obj.name = new_name
    obj.data.name = f"{new_name}"+"_mesh"

def bridgeLoopMeshes(type, sub_num, savepath):
    """
    Bridge loop meshes and fill holes.

    Parameters
    ----------
    type : string
        Type of mesh (e.g., 'Dura', 'Cord')
    """
    # Select all mesh objects and enter edit mode
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.object.select_by_type(type='MESH')
    bpy.ops.object.mode_set_with_submode(mode='EDIT')
    bpy.ops.mesh.select_all(action = 'SELECT')
    
    # Bridge edge loops
    bpy.ops.mesh.bridge_edge_loops(number_cuts=6, interpolation='SURFACE')
    
    # Fill holes
    bpy.ops.mesh.select_mode(type="VERT")
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.select_non_manifold(extend=False, use_wire=True)
    bpy.ops.mesh.edge_face_add()
    
    # Recover to vertex select mode and object mode
    bpy.ops.mesh.select_mode(type="VERT")
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    
    # Save mesh as STL
    bpy.ops.object.select_by_type(type='MESH')
    bpy.ops.export_mesh.stl(filepath=os.path.join(savepath,f"{sub_num}_{type}.stl"), use_selection=True)
    
def establishMesh_pyvista(stl_path):
    """
    Read STL file and subdivide mesh.

    Parameters
    ----------
    stl_path : string
        Path to the STL file

    Returns
    -------
    model : pyvista.PolyData
        Subdivided mesh
    """
    # Read STL file
    meshes = pv.read(stl_path)
    
    # Set number of subdivisions (adjust as needed)
    num_subdivisions = 3
    
    # Subdivide mesh
    model = meshes[0].subdivide(num_subdivisions)  # meshes[0] is voxel size (spacing)
    
    return model

def getEntryPoints(lines):
    """
    Get entry points of marked nerves.

    Parameters
    ----------
    lines : list of arrays
        List containing arrays representing nerve lines

    Returns
    -------
    entrypoints : array
        Array of entry points of marked nerves
    """
    entrypoints = np.empty((len(lines), 3))  # Entry point: first points of a marked nerve
    for i in range(len(lines)):
        entrypoints[i] = lines[i][0]
    return entrypoints

def reloc_entrypoint(cordstl_path, lines):
    """
    Relocate entry points of nerve lines based on the closest points on the mesh.

    Parameters
    ----------
    cordstl_path : string
        Path to the cord STL file
    lines : list of arrays
        List containing arrays representing nerve lines

    Returns
    -------
    relocentry_lines : list of arrays
        List containing arrays representing relocated nerve lines
    """
    # Establish mesh from STL file
    model = establishMesh_pyvista([cordstl_path])
    
    # Get entry points of nerve lines
    entrypoints = getEntryPoints(lines)
    
    # Initialize list for relocated nerve lines
    relocentry_lines = []
    
    # Iterate over nerve lines
    for i in range(len(lines)):
        # Find the point on the mesh closest to the entry point
        closest_point = model.points[model.find_closest_point(entrypoints[i])]
        
        # Create a slice containing the closest point
        sliced_mesh = model.slice(normal='z', origin=closest_point)
        center = np.array(sliced_mesh.center)  # Find the center point
        
        # Calculate the inner point between the closest point and the center
        inner_point = closest_point + (center - closest_point) / 4 * 3
        
        # Insert the inner point and the closest point before the original line
        relocentry_line = np.insert(lines[i], 0, np.vstack((inner_point, closest_point)), 0)
        relocentry_lines.append(relocentry_line)
    
    return relocentry_lines

def smoothingLine(line, n_interpolate, s=None):
    """
    Smooth a line by interpolating its points.

    Parameters
    ----------
    line : array
        Array representing the line with x, y, and z coordinates
    n_interpolate : int
        Number of points to interpolate between existing points
    s : float, optional
        Parameter controlling the spline fitting. Larger s means more smoothing,
        while smaller s values indicate less smoothing.

    Returns
    -------
    line_smoothed : array
        Array representing the smoothed line
    """

    x = line[:, 0]
    y = line[:, 1]
    z = line[:, 2]
    
    # Interpolate the line
    tck, u = splprep([x, y, z], s=s)
    smoothed_points = splev(np.linspace(0, 1, n_interpolate), tck)
    
    # Combine them back into the original format
    line_smoothed = np.column_stack((smoothed_points[0], smoothed_points[1], smoothed_points[2]))
    
    return line_smoothed

def smoothingLines(lines, n_interpolate, s=None):
    """
    Smooth multiple lines by interpolating their points.

    Parameters
    ----------
    lines : list of arrays
        List containing arrays representing lines with x, y, and z coordinates
    n_interpolate : int
        Number of points to interpolate between existing points
    s : float, optional
        Parameter controlling the spline fitting. Larger s means more smoothing,
        while smaller s values indicate less smoothing.

    Returns
    -------
    lines_smoothed : list of arrays
        List containing arrays representing the smoothed lines
    """
    lines_smoothed = []
    
    # Iterate over lines
    for i in range(len(lines)):
        # Smooth the line
        line_smoothed = smoothingLine(lines[i], n_interpolate, s)
        
        # Append the smoothed line to the list
        lines_smoothed.append(line_smoothed)
    
    return lines_smoothed

def getnsaveMeshOpenSplines(lines, SEG, Rs, sub_num, savepath):
    """
    Create splines, save as STL.

    Parameters
    ----------
    lines : list of arrays
        List containing arrays representing lines
    SEG : list of strings
        List containing segment identifiers
    Rs : list of floats
        List containing radii of the splines
    """
    # Initialize arrays for top normals and centers
    lines_top_normal = np.empty((len(lines), 3))
    lines_top_center = np.empty((len(lines), 3))
    
    # Select collection to add objects
    collection_name = "Collection"
    selected_collection = bpy.context.scene.collection.children.get(collection_name)
    
    # Iterate over lines
    for i in range(len(lines)):
        # Create curve object
        if i % 2 == 0:
            curve = bpy.data.curves.new(name=f"{SEG[i//2]}_L_Line", type='CURVE')
        else:
            curve = bpy.data.curves.new(name=f"{SEG[i//2]}_R_Line", type='CURVE')
        curve.dimensions = '3D'
        curve.bevel_depth = Rs[i//2]
        curve.bevel_resolution = 16
        
        # Create object from curve
        if i % 2 == 0:
            obj = bpy.data.objects.new(f"{SEG[i//2]}_L_line", curve)
        else:
            obj = bpy.data.objects.new(f"{SEG[i//2]}_R_line", curve)
        
        # Link object to collection
        if selected_collection:
            selected_collection.objects.link(obj)
        else:
            print(f"Collection '{collection_name}' not found.")
        
        # Create spline
        spline = curve.splines.new(type='NURBS')
        spline.radius_interpolation = 'CARDINAL'
        spline.tilt_interpolation = 'CARDINAL'
        spline.points.add(len(lines[i]) - 1)
        for j, coord in enumerate(lines[i]):
            spline.points[j].co = (coord[0], coord[1], coord[2], 1)
        
        # Convert curve to mesh
        bpy.ops.object.select_all(action='DESELECT')
        if i % 2 == 0:
            bpy.context.view_layer.objects.active = bpy.data.objects[f"{SEG[i//2]}_L_line"]
            bpy.data.objects[f"{SEG[i//2]}_L_line"].select_set(True)
        else:
            bpy.context.view_layer.objects.active = bpy.data.objects[f"{SEG[i//2]}_R_line"]
            bpy.data.objects[f"{SEG[i//2]}_R_line"].select_set(True)
        bpy.ops.object.convert(target='MESH')
        
        # Fill holes
        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.object.select_by_type(type='MESH')
        bpy.ops.object.mode_set_with_submode(mode='EDIT')
        bpy.ops.mesh.select_mode(type="VERT")
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.select_non_manifold(extend=False, use_wire=True)
        bpy.ops.mesh.edge_face_add()
        bpy.ops.mesh.select_mode(type="FACE")
        
        # Recover to vertex select mode and object mode
        bpy.ops.mesh.select_mode(type="VERT")
        bpy.ops.object.mode_set(mode='OBJECT')
    
    # Update scene
    bpy.context.view_layer.update()
    
    # Join all curve meshes into one mesh
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.object.select_by_type(type='MESH')
    bpy.ops.object.join()
    
    # Rename joined mesh
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.object.select_by_type(type='MESH')
    obj = bpy.context.selected_objects[0]
    new_name = f"{sub_num}_Nerveroots"
    obj.name = new_name
    obj.data.name = f"{new_name}"+"_mesh"
    
    # Save mesh as STL
    bpy.ops.object.select_by_type(type='MESH')
    bpy.ops.export_mesh.stl(filepath=os.path.join(savepath,f"{sub_num}_Nerveroots.stl"), use_selection=True)