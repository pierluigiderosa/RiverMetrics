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
from PyQt4.QtCore import QVariant

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

def directSinuosity(geom,pt1_station,pt2_station):
    startPoint = pointAtDist(geom,pt1_station)
    endPoint = pointAtDist(geom,pt2_station)
    distance = qgisdist(startPoint,endPoint)
    length_reach = pt2_station-pt1_station
    return length_reach/distance


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

def createMemLayer():
    # create layer
    vl = QgsVectorLayer("LineString", "temporary_river", "memory")
    pr = vl.dataProvider()
    # add fields
    pr.addAttributes([QgsField("reach", QVariant.String),
                      QgsField("sinuosity", QVariant.Double),
                      QgsField("size", QVariant.Int)])
    vl.updateFields()  # tell the vector layer to fetch changes from the provider

    # add a feature
    fet = QgsFeature()
    fet.setGeometry(QgsGeometry.fromPoint(QgsPoint(10, 10)))
    fet.setAttributes(["Johny", 2, 0.3])
    pr.addFeatures([fet])

    # update layer's extent when new features have been added
    # because change of extent in provider is not propagated to the layer
    vl.updateExtents()
