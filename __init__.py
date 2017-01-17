# -*- coding: utf-8 -*-
"""
/***************************************************************************
 RiverMetrics
                                 A QGIS plugin
 description
                             -------------------
        begin                : 2017-01-09
        copyright            : (C) 2017 by pierluigi de rosa
        email                : pierluigi.derosa@gmail.com
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load RiverMetrics class from file RiverMetrics.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .river_metrics import RiverMetrics
    return RiverMetrics(iface)
