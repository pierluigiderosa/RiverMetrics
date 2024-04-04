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
from qgis.core import QgsFeature, QgsVectorLayer, QgsField, QgsPoint,QgsProject,QgsGeometry

from qgis.PyQt.QtCore import QVariant, QCoreApplication
from qgis.utils import iface
import numpy as np
# from utils import *
from .geometry import *


def createPointsAt(distance, geom):
    length = geom.length()
    currentdistance = distance
    feats = []

    while currentdistance < length:
        # Get a point along the line at the current distance
        point = geom.interpolate(currentdistance)
        # Create a new QgsFeature and assign it the new geometry
        fet = QgsFeature()
        fet.setAttributes([0, currentdistance])
        fet.setGeometry(point)
        feats.append(fet)
        # Increase the distance
        currentdistance = currentdistance + distance

    return feats


def pointsAlongLine(distance):
    """Create a new memory layer and add a distance attribute"""
    vl = QgsVectorLayer("Point", "distance nodes", "memory")
    pr = vl.dataProvider()
    pr.addAttributes([QgsField("distance", QVariant.Int)])
    layer = iface.mapCanvas().currentLayer()
    vl.setCrs(layer.crs())
    # Loop though all the selected features
    for feature in layer.getFeatures():
        geom = feature.geometry()
        features = createPointsAt(distance, geom)
        pr.addFeatures(features)
        vl.updateExtents()

    # QgsProject.instance().addMapLayer.addMapLayer(vl)


def create_XS_secs(layer, step=1000, sez_length=1000):
    """
    Function to create point at specified distance from initial point line
    author: Giovanni Allegri email: giohappy@gmail.com
    """
    crs = layer.crs()
    if layer:
        pt_mid = QgsVectorLayer("Point", "distance nodes", "memory")
        pt_mid.setCrs(crs)
        pr = pt_mid.dataProvider()
        # pr.addAttributes([QgsField("name", QVariant.String),
        #                   QgsField("age", QVariant.Int),
        #                   QgsField("size", QVariant.Double)])
        pr.addAttributes([QgsField("distance", QVariant.Double)])
        pt_mid.updateFields()

        pt_feats = []

        sez = QgsVectorLayer("LineString",
            str(QCoreApplication.translate("dialog", "Cross section")), "memory"
        )
        sez.setCrs(crs)
        pr_sez=sez.dataProvider()
        pr_sez.addAttributes([QgsField("distance", QVariant.Double)])
        sez.updateFields()
        pr_sez_feats = []

        for elem in layer.getFeatures():
            line = elem.geometry()
            line_length = 0
            currentDistance = step
            for seg_start, seg_end in paires(line.asPolyline()):
                line_start = QgsPoint(seg_start)
                line_end = QgsPoint(seg_end)
                pointm = diff(line_end, line_start)
                cosa, cosb = cosdir(pointm)
                seg_length = dist(line_end, line_start)
                while (line_length + seg_length) >= currentDistance:
                    step_length = currentDistance - line_length
                    p0 = line_start.x() + (step_length * cosa)
                    p1 = line_start.y() + (step_length * cosb)
                    p = QgsPoint(p0, p1)
                    # Create a new QgsFeature for midpoints and assign it the new geometry
                    fet = QgsFeature()
                    fet.setAttributes([currentDistance])
                    fet.setGeometry(p)
                    pt_feats.append(fet)

                    XSline = get_profile_seg(
                        line_start, line_end, p, sez_length
                    )
                    fetXS = QgsFeature()
                    fetXS.setAttributes([currentDistance])
                    fetXS.setGeometry(XSline)
                    pr_sez_feats.append(fetXS)
                    # sez.add_line(prof_st, prof_end)
                    currentDistance += step
                line_length += seg_length

        # add features to mid points
        pr.addFeatures(pt_feats)
        pt_mid.updateExtents()
        #QgsProject.instance().addMapLayer(pt_mid)

        # add feature do XS
        pr_sez.addFeatures(pr_sez_feats)
        sez.updateExtents()
        #QgsProject.instance().addMapLayer(sezioni)

        return pt_mid,sez


def get_profile_seg(p0, p1, mid, length):
    """
    Function to create XS at specified distance from initial point line
    author: Giovanni Allegri email: giohappy@gmail.com"""

    disp = np.array([[p1.x() - p0.x()], [p1.y() - p0.y()]])
    rot_anti = np.array([[0, -1], [1, 0]])
    rot_clock = np.array([[0, 1], [-1, 0]])
    vec_anti = np.dot(rot_anti, disp)
    vec_clock = np.dot(rot_clock, disp)
    len_anti = ((vec_anti**2).sum()) ** 0.5
    vec_anti = vec_anti / len_anti
    len_clock = ((vec_clock**2).sum()) ** 0.5
    vec_clock = vec_clock / len_clock
    vec_anti = vec_anti * length
    vec_clock = vec_clock * length
    prof_st = QgsPoint(mid.x() + float(vec_anti[0]), mid.y() + float(vec_anti[1]))
    prof_end = QgsPoint(mid.x() + float(vec_clock[0]), mid.y() + float(vec_clock[1]))
    XSline = QgsGeometry.fromPolyline([prof_st, prof_end])
    return XSline
