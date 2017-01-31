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
from tools import sinuosity,createMemLayer

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
        self.graphicState = False
        self.canvas = None
        self.figure = None
        self.breaks = [] # breaks of river axes
        self.line= None # line geometry
        self.breakButton = QtGui.QPushButton('Add breaks')
        self.breakButton.setCheckable(True)
        self.breakButton.clicked.connect(self.addBreaks)




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
            self.message(vlayer.name()+' is valid','white')

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

        #TODO -- add validate CRS layer to be not a geographic

    def clearLayout(self,layout):
        '''
        clera layout function
        :return:
        '''
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def graph_data(self):
        if self.graphicState is True:
            self.canvas = None
            self.figure = None
            self.clearLayout(self.layout)
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
                self.line = the_geom

            #create a new empty QVboxLayout
            self.layout = QtGui.QVBoxLayout()

            #set the Qframe layout
            self.frame_for_plot.setLayout(self.layout)
            self.figure = plt.figure()
            self.canvas = FigureCanvas(self.figure)
            self.layout.addWidget(self.canvas)
            self.layout.addWidget(self.breakButton)
            ax = self.figure.add_subplot(111)
            ax.plot(x, y, 'bo', x, y, 'k')


            #def addVline():
            #if breakButton.isChecked():
             #       figure.canvas.mpl_connect('button_press_event', OnClick)

            self.canvas.show()
            #set variable graphState to true to remember graph is plotted
            self.graphicState=True

            #self.graph.hide()

    def addBreaks(self):

        def OnClick(event):
            ax=self.figure.add_subplot(111)
            ax.axvline(event.xdata,linewidth=4, color='r')
            self.canvas.draw()
            self.breaks.append(float(event.xdata))

        if self.graphicState is True:
            if self.breakButton.isChecked():
                self.breakButton.setText('stop-break')
                self.cid = self.figure.canvas.mpl_connect('button_press_event', OnClick)
            #TODO: create memory layer splitted with breaks
            else:
                self.breakButton.setText('Add Break')
                self.figure.canvas.mpl_disconnect(self.cid)
                self.final()
                #print self.breaks
                # ll1 = createMemLayer(self.line, self.breaks)
                # QgsMapLayerRegistry.instance().addMapLayers([ll1])
        else:
            self.message('You have to graph your data first','yellow')

    def final(self):

        index = self.vectorCombo.currentIndex()
        vlayer = self.vectorCombo.itemData(index)
        for feat in vlayer.getFeatures():
            the_geom = feat.geometry()
        #TODO: remove the line for debigging
        #self.message(str(vlayer.name())+'|'+str(the_geom.length())+'|'+str(self.breaks), 'red')

        ll1 = createMemLayer(the_geom, self.breaks)
        QgsMapLayerRegistry.instance().addMapLayer(ll1)





