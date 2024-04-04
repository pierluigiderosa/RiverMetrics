# -*- coding: utf-8 -*-
"""
/***************************************************************************
 RiverMetrics
                                 A QGIS plugin
 description
                              -------------------
        begin                : 2024-02-24
        git sha              : $Format:%H$
        copyright            : (C) 2024 by pierluigi de rosa
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
from builtins import str
from builtins import range
from qgis._core import (QgsFeature, QgsGeometry,
                        QgsVectorLayer,
                        QgsField)
from math import sqrt
from qgis.PyQt.QtCore import QVariant
import pandas as pd

def pointAtDist(geom, distance):
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


def bradingIndex(XSlayer, channel, step, win_size):
    X = []
    Y = []

    Xval = []
    Yval = []

    for XSfeat in XSlayer.getFeatures():
        the_geom = XSfeat.geometry()
        request = the_geom.boundingBox()
        for f in channel.getFeatures(request):
            poly_geom = f.geometry()
            if poly_geom.intersects(the_geom):
                intersezione = the_geom.intersection(poly_geom)
                if intersezione.isMultipart():
                    chann = intersezione.asMultiPolyline()
                    nchann = len(chann)
                else:
                    chann = intersezione.asPolyline()
                    nchann = len(chann) / 2
                Xval.append(float(XSfeat['distance']))
                Yval.append(nchann)

        # determino la dimensione della finestra mobile
    window_size = int(win_size / step)

    if len(Yval) <= window_size:
        X.append(Xval)
        Y.append(sum(Yval) / len(Yval))
    for i in range(len(Yval) - window_size + 1):
        sublist = Yval[i:i + window_size]
        sub_prog = Xval[i:i + window_size]
        ampiezza = max(sub_prog) - min(sub_prog)
        X.append(min(sub_prog) + ampiezza / 2)
        Y.append(sum(sublist) / len(sublist))

    return X, Y

def sinuosity(geom, step, shift):
    '''

    :param geom: QGis geometry type
    :param step: lenght of reach
    :param shift: downstream shift
    :return: sinuosity value
    '''
    initStation = 0
    endStation = step
    midStation = step / 2.
    riverLeng = geom.length()
    Xval = []
    Yval = []

    # TODO this line for debug
    #f = open('/tmp/workfile.csv', 'w')

    while endStation <= riverLeng:
        startPoint = pointAtDist(geom, initStation)
        endPoint = pointAtDist(geom, endStation)
        distance = qgisdist(startPoint, endPoint)
        sinuosity = step / distance
        Xval.append(midStation, )
        Yval.append(sinuosity)
        # TODO this line for debug
        #f.write(str(midStation) + ',' + str(sinuosity) + '\n')
        initStation += shift
        endStation += shift
        midStation += shift
    return Xval, Yval


def splitLine(line, ptInit, ptEnd):
    puntoInit = ptInit.asPoint()
    puntoEnd = ptEnd.asPoint()
    sqrDistInit, minDistPointInit, afterVertexInit , leftOf = line.closestSegmentWithContext(puntoInit)
    sqrDistEnd, minDistPointEnd, afterVertexEnd , leftOf = line.closestSegmentWithContext(puntoEnd)
    if line.isMultipart():
        pline=line.asMultiPolyline()[0]
    else:
        pline = line.asPolyline()
    newPoints = []
    newPoints.append(minDistPointInit)
    for iter in range(afterVertexInit, afterVertexEnd):
        newPoints.append(pline[iter])
    newPoints.append(minDistPointEnd)
    return newPoints



def createMemLayer(line,breaksList,crs=None):
    '''
    create memory layer storing all reaches
    :return:
    '''
    # create layer
    vl = QgsVectorLayer("LineString", "sinuosity_river", "memory")
    vl.setCrs(crs)
    pr = vl.dataProvider()
    # add fields
    pr.addAttributes([QgsField("reach", QVariant.Int),
                      QgsField("sinuosity", QVariant.Double),
                      QgsField("Length", QVariant.Double)])
    vl.updateFields()
    # create breaks with initial and final
    bk=sorted(breaksList)
    bk.insert(0, 0)
    bk.append(line.length())
    for breack in range(1,len(bk)):
        ptInt = line.interpolate(bk[breack-1])
        ptFin = line.interpolate(bk[breack])
        reach = splitLine(line,ptInt,ptFin)
        # sinuosity calc
        dist=qgisdist(ptInt,ptFin)
        lenReach=bk[breack]-bk[breack-1]
        # add a feature
        fet = QgsFeature()
        fet.setGeometry(QgsGeometry.fromPolylineXY(reach))
        fet.setAttributes([breack, lenReach/dist, str(lenReach)])
        pr.addFeatures([fet])
    #vl.updateExtents()
    vl.commitChanges()
    return vl

def createBradingLayer (line,breaksList,X,Y,crs=None):
    '''
        create memory layer storing all reaches for braiding index
        :return:
        '''
    vl = QgsVectorLayer("LineString", "braiding_river", "memory")
    vl.setCrs(crs)
    pr = vl.dataProvider()
    # add fields
    pr.addAttributes([
        QgsField("reach", QVariant.String),
                      QgsField("braiding", QVariant.Double),
                      QgsField("Length", QVariant.Double)])
    vl.updateFields()
    print(f"{vl.isValid()=}")
    feat_list = []
    reach_list = []
    attr_list=[]


    breaksList.append(0)
    breaksList.append(line.length())
    bk = sorted(breaksList)

    df = pd.DataFrame()
    df["stationing"] = X  ## assegno i valori alle colonne tramite liste
    df["nchann"] = Y
    df['id'] = None
    for breakval in range(len(bk) - 1):

        ptInt = line.interpolate(bk[breakval])
        ptFin = line.interpolate(bk[breakval+1])
        reach = splitLine(line, ptInt, ptFin)
        # pippo

        df['id'][(df["stationing"] >= bk[breakval]) & (df["stationing"] < bk[breakval + 1])] = breakval
        sel = df[(df["stationing"] >= bk[breakval]) & (df["stationing"] < bk[breakval + 1])]
        brIndex = float(sel['nchann'].mean())
        lenReach = float(bk[breakval+1] - bk[breakval])
        # add a feature
        fet = QgsFeature()
        the_geom = QgsGeometry.fromPolylineXY(reach)
        fet.setGeometry(the_geom)
        fet.setAttributes([ str(breakval),   brIndex,  lenReach])
        print(f"{breakval}+{fet.isValid()=}")
        # pr.addFeature(fet)
        # vl.updateExtents()
        print(breakval, brIndex, lenReach,sep='-')
        feat_list.append(fet)
        reach_list.append(reach)
        attr_list.append([ str(breakval),  brIndex, lenReach])



    # vl.commitChanges()

    (result, newFeatures) = pr.addFeatures(feat_list)

    print(f"{result=}")
    print(newFeatures)

    return vl
