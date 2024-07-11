import bpy

def initialize():
    """
    Initialize Blender scene by clearing all objects and hiding default camera and light source.
    """

    # Clear all objects in the scene
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.object.select_by_type(type='MESH')
    bpy.ops.object.delete()
    
    # Hide default camera
    camera = bpy.data.objects.get("Camera")
    if camera:
        camera.hide_viewport = True
    
    # Hide default light source
    light = bpy.data.objects.get("Light")
    if light:
        light.hide_viewport = True

def clearMesh():
    """
    Clear all mesh objects in the scene.
    """

    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.object.select_by_type(type='MESH')
    bpy.ops.object.delete()