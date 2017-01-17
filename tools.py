# -*- coding: utf-8 -*-
"""
/***************************************************************************
 RiverMetrics
                                 A QGIS plugin
 description
                              -------------------
        begin                : 2017-01-09
        git sha              : $Format:%H$
        copyright            : (C) 2017 by pierluigi de rosa
        email                : pierluigi.derosa@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from qgis._core import (QgsFeature, QgsGeometry,
                        QgsVectorLayer, QgsMapLayerRegistry,
                        QgsField)
from math import sqrt

def pointAtDist(geom,distance):
    length = geom.length()
    if distance < length:
        point = geom.interpolate(distance)
    else:
        point = None
    return point


def qgisdist(point1, point2):
    point1 = point1.asPoint()
    point2 = point2.asPoint()
    return sqrt(point1.sqrDist(point2))




def sinuosity(geom,step,shift):
    '''

    :param geom: QGis geometry type
    :param step: lenght of reach
    :param shift: downstream shift
    :return: sinuosity value
    '''
    initStation = 0
    endStation = step
    midStation = step/2.
    riverLeng = geom.length()
    Xval = []
    Yval = []

    #TODO this line for debug
    f = open('/tmp/workfile.csv', 'w')

    while endStation <= riverLeng:
        startPoint = pointAtDist(geom,initStation)
        endPoint = pointAtDist(geom,endStation)
        distance = qgisdist(startPoint,endPoint)
        sinuosity = step/distance
        Xval.append(midStation,)
        Yval.append(sinuosity)
        # TODO this line for debug
        f.write(str(midStation)+','+str(sinuosity)+'\n')
        initStation += shift
        endStation += shift
        midStation += shift
    return Xval,Yval