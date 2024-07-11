import numpy as np
import pandas as pd
import os


def getCurvePosition(file_path):
    """
    Get position data from a JSON file representing a curve

    Parameters
    ----------
    file_path : string
        Path to the JSON file containing markup data

    Returns
    -------
    position : array
        Array of position data representing the curve
    """
    
    source = pd.DataFrame.from_dict(pd.read_json(file_path)['markups'][0]['controlPoints'])
    position = np.array([np.array(i) for i in source['position']])
    return position

def getCurveHeight(positionList):
    """
    Get the height of the first point in a position list

    Parameters
    ----------
    positionList : array
        Array of position data representing a curve

    Returns
    -------
    height : float
        Height of the first point in the position list
    """
        
    return positionList[0][2]

def getOutpoint(file_path):
    """
    Get the position of the exit point (ganglion point) for a given segment line

    Parameters
    ----------
    file_path : string
        Path to the JSON file containing markup data

    Returns
    -------
    position : array
        Array of position data representing the exit point
    """

    source = pd.DataFrame.from_dict(pd.read_json(file_path)['markups'][0]['controlPoints'])
    position = np.array([np.array(i) for i in source['position']])
    if len(source) >= 2:
        position = np.delete(position, 0, axis=0)
    return position

def getOtherPosition(file_path):
    """
    Get nerveroots position data of one segment from a JSON file
    
    Parameters
    ----------
    file_path : string
        Path to the JSON file
    
    Returns
    -------
    position : array
        Array of position data sorted in descending order of z-axis
    """
    
    source = pd.DataFrame.from_dict(pd.read_json(file_path)['markups'][0]['controlPoints'])
    position = np.array([np.array(i) for i in source['position']])
    position = position[np.lexsort(-position.T)]  # 对position按照z轴从大到小排序
    return position

def getLinesPositionList(file_path_base, sub_num, SEG):
    """
    Get the position list of nerve lines for each SEG segment
    
    Parameters
    ----------
    file_path_base : string
        Base path where nerveroots lines data is stored
    sub_num : string
        Participant ID
    SEG : string list
        list of targeted segments
    
    Returns
    -------
    plist : list
        List of position lists of nerve lines for each segment
    """

    plist = []
    for i in range(len(SEG)):
        # seg left
        nerveroot_file_path = os.path.join(file_path_base, sub_num+'_nerveroots_'+SEG[i]+'_L'+'.json')
        position = getOtherPosition(nerveroot_file_path)
        ganglion_file_path = os.path.join(file_path_base, sub_num+'_ganglions_'+SEG[i]+'_L'+'.json')
        outpoint = getOutpoint(ganglion_file_path)
        position = np.vstack((position, outpoint))
        plist.append(position)
        # seg right
        nerveroot_file_path = os.path.join(file_path_base, sub_num+'_nerveroots_'+SEG[i]+'_R'+'.json')
        position = getOtherPosition(nerveroot_file_path)
        ganglion_file_path = os.path.join(file_path_base, sub_num+'_ganglions_'+SEG[i]+'_R'+'.json')
        outpoint = getOutpoint(ganglion_file_path)
        position = np.vstack((position, outpoint))
        plist.append(position)
    return plist


def importPoints(annotation_base_path, SEG, sub_num):
    """
    Load and preprocess annotation data for a specific participant

    Parameters
    ----------
    annotation_base_path : string
        Base path where annotation data is stored
    SEG : string list
        list of targeted segments
    sub_num : string
        Participant ID

    Returns
    -------
    dura : list
        List of positions of dura curves
    cord : list
        List of positions of cord curves
    lines : list
        List of positions of nerve lines
    """

    if not os.path.exists(annotation_base_path):
        print(f"Path not exist: {annotation_base_path}")
        return
    
    # find the annotation path of the participant
    for Root, directories, files in os.walk(annotation_base_path):
        for directory in directories:
            if directory == sub_num:
                annotation_path = os.path.join(Root, directory)
                break
    
    # import dura and cord curves
    dura = []
    cord = []
    for root, directories, files in os.walk(annotation_path):
        for file in files:
            if "cord" in file:
                cord.append(getCurvePosition(os.path.join(annotation_path, file)))
            elif "dura" in file:
                dura.append(getCurvePosition(os.path.join(annotation_path, file)))
    dura.sort(key=getCurveHeight, reverse=True)
    cord.sort(key=getCurveHeight, reverse=True)

    # import nerve lines
    lines = getLinesPositionList(annotation_path, sub_num, SEG)
    
    return dura, cord, lines