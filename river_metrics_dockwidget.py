# -*- coding: utf-8 -*-
"""
/***************************************************************************
 RiverMetricsDockWidget
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

import os

from PyQt4 import QtGui, uic
from PyQt4.QtCore import pyqtSignal
import sys
sys.path.append(os.path.dirname(__file__))
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'river_metrics_dockwidget_base.ui'), resource_suffix='')

#FORM_CLASS, _ = uic.loadUiType(os.path.join(
#    os.path.dirname(__file__), 'river_metrics_dockwidget_base.ui'))
from qgis._core import QgsMapLayer,QGis
from qgis._core import QgsMapLayerRegistry
from tools import sinuosity

# import mathplotlib libraries
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar
import matplotlib.pyplot as plt

class RiverMetricsDockWidget(QtGui.QDockWidget, FORM_CLASS):

    closingPlugin = pyqtSignal()

    def __init__(self, parent=None):
        """Constructor."""
        super(RiverMetricsDockWidget, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        self.setup_gui()
        self.validate.clicked.connect(self.validateLayer)
        self.graph.clicked.connect(self.graph_data)
        #self.vectorCombo.currentIndexChanged.connect(self.setup_gui)

        #global variables
        self.validate_test = None



    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()

    def message(self,text,col):
        self.validator.setText(text)
        self.validator.setStyleSheet('background-color: '+col)



    def setup_gui(self):
        '''clear validator message'''
        self.validator.clear()
        """ Function to combos creation """
        self.vectorCombo.clear()
        layers = QgsMapLayerRegistry.instance().mapLayers().values()
        layerRasters = []
        layerVectors = []
        for layer in layers:
            if layer.type() == QgsMapLayer.VectorLayer:
                self.vectorCombo.addItem(layer.name(), layer)

    def validateLayer(self):
        self.validator.clear()
        self.validator.setStyleSheet('background-color: None')
        index = self.vectorCombo.currentIndex()
        vlayer = self.vectorCombo.itemData(index)


        if not vlayer.isValid():
            self.message(vlayer.name()+' is not valid','red')
            self.validate_test=False
        elif vlayer.geometryType() != QGis.Line:
            self.message('your vector layer is not a Line','red')
            self.validate_test = False
        else:
            self.validate_test = True

        if vlayer.featureCount() > 1:
            self.message('You have more then one feature on your vector layer','yellow')
            self.validate_test = False
        else:
            for feat in vlayer.getFeatures():
                the_geom = feat.geometry()
                len = the_geom.length()
                self.validate_test = True
                if self.stepSpin.value() >= the_geom.length():
                    self.message('Use a smaller value for step less than ' +
                                 str(round(len/1000,2)) + ' km', 'yellow')
                    self.validate_test = False



    def graph_data(self):
        step = self.stepSpin.value()
        shif = self.shiftSpin.value()
        if self.validate_test == None:
            self.message('You have to validate your layers first','yellow')
        if self.validate_test == True:
            index = self.vectorCombo.currentIndex()
            vlayer = self.vectorCombo.itemData(index)
            for feat in vlayer.getFeatures():
                the_geom = feat.geometry()
                x,y = sinuosity(the_geom,step ,shif)

        #create a new empty QVboxLayout
        layout = QtGui.QVBoxLayout()
        #set the Qframe layout
        self.frame_for_plot.setLayout(layout)
        figure = plt.figure()
        canvas = FigureCanvas(figure)
        layout.addWidget(canvas)
        ax = figure.add_subplot(111)
        ax.plot(x, y, 'bo', x, y, 'k')
        canvas.draw()

