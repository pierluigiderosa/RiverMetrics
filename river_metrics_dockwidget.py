# -*- coding: utf-8 -*-
"""
/***************************************************************************
 RiverMetricsDockWidget
                                 A QGIS plugin
 The plugin allows to calculate the river metrcics
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2024-02-21
        git sha              : $Format:%H$
        copyright            : (C) 2024 by Pierluigi De Rosa e Andrea Fredduzzi
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

from qgis.PyQt import QtGui, QtWidgets, uic
from qgis.PyQt.QtCore import pyqtSignal

from qgis.PyQt.QtWidgets import QFileDialog,  QPushButton,QVBoxLayout
from PyQt5.QtWidgets import QMainWindow, QDockWidget

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'river_metrics_dockwidget_base.ui'))

from qgis._core import QgsMapLayer,  QgsWkbTypes, QgsMapLayerProxyModel
from qgis._core import QgsProject
from .tools import sinuosity,createMemLayer,bradingIndex,createBradingLayer
from .transect.XSGenerator import create_XS_secs

# import mathplotlib libraries
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
import tempfile

class RiverMetricsDockWidget(QtWidgets.QDockWidget, FORM_CLASS):

    closingPlugin = pyqtSignal()

    def __init__(self, parent=None):
        """Constructor."""
        super(RiverMetricsDockWidget, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://doc.qt.io/qt-5/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)

        # LINK segnale toggled ai rispettivi slot
        self.sinuosityRadio.toggled.connect(self.onRadioToggled)
        self.profilesRadio.toggled.connect(self.onRadioToggled)

        # Set sinuosityRadio already activate on startup
        self.sinuosityRadio.setChecked(True)

        # fill the layer combobox with vector layers
        self.vectorCombo.setFilters(QgsMapLayerProxyModel.LineLayer)
        self.RiverLayerComboBox.setFilters(QgsMapLayerProxyModel.LineLayer)
        self.validate.clicked.connect(self.validateLayer)
        self.validateBraiding.clicked.connect(self.validateLayerOtherIndex)
        self.graph.clicked.connect(self.graph_data)
        self.braidingGraph.clicked.connect(self.graph_braiding)
        self.transectButton.clicked.connect(self.transect)
        

        self.clear_graph.clicked.connect(self.do_clear_graph)
        self.clear_graph1.clicked.connect(self.do_clear_graph1)
        # self.vectorCombo.currentIndexChanged.connect(self.setup_gui)

        # global variables
        self.validate_test = None
        self.XSgenerated= False
        self.graphicState = False
        self.canvas = None
        self.figure = None
        self.canvas1 = None
        self.figure1 = None
        self.breaks = []  # breaks of river axes in sinuosity
        self.breaks1 = []  # breaks of river axes in braiding
        self.line = None  # line geometry
        self.breakButton = QPushButton('Add breaks sinuosity')
        self.breakButton.setCheckable(True)
        self.breakButton1 = QPushButton('Add breaks braiding')
        self.breakButton1.setCheckable(True)
        self.Xcsv = None
        self.Ycsv = None
        self.layerXS = None
        self.X = None #variable for stationing XS
        self.Y = None #variable for nchannel in XS
        self.breakButton.clicked.connect(self.addBreaks)
        self.breakButton1.clicked.connect(self.addBreaks1)
        self.browseBtn.clicked.connect(self.writeFile)


        # create container plot
        self.setup_gui()

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()
        
    def message(self,text,col,Qlabel):
        Qlabel.setText(text)
        Qlabel.setStyleSheet('background-color: '+col)
        
    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()

    def onRadioToggled(self):
        # Determina quale radio button è stato selezionato
        sender = self.sender()

        # Ottieni l'indice della pagina associata al radio button
        index = 0 if sender == self.sinuosityRadio else 1

        # Mostra la pagina corrispondente nello stacked widget
        self.stackedWidget.setCurrentIndex(index)

    def setup_gui(self):

        #PLOT container
        # a figure instance to plot on
        self.figure = plt.figure()
        self.figure1 = plt.figure()

        # this is the Canvas Widget that displays the `figure`
        # it takes the `figure` instance as a parameter to __init__
        self.canvas = FigureCanvas(self.figure)
        self.canvas1 = FigureCanvas(self.figure1)

        # this is the Navigation widget
        # it takes the Canvas widget and a parent
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.toolbar1 = NavigationToolbar(self.canvas, self)

        #  create a new empty QVboxLayout
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.toolbar)
        self.layout.addWidget(self.canvas)
        self.layout.addWidget(self.breakButton)

        self.layout1 = QVBoxLayout()
        self.layout1.addWidget(self.toolbar1)
        self.layout1.addWidget(self.canvas1)
        self.layout1.addWidget(self.breakButton1)

        # set the Qframe layout
        self.frame_for_plot.setLayout(self.layout)
        self.frame_for_plot_2.setLayout(self.layout1)


    def validateLayerOtherIndex(self):
        self.validatorBraiding.clear()
        self.validatorBraiding.setStyleSheet('background-color: None')
        riverAxes = self.RiverLayerComboBox.currentLayer()
        channelLayer = self.channelLayerComboBox.currentLayer()
        message, color = self.checkLayerAxes(riverAxes)
        message1, color = self.checkPolyLayer(riverAxes,channelLayer)
        self.message(message+' '+message1, color, self.validatorBraiding)


    def validateLayer(self):
        self.validatorSinuosity.clear()
        self.validatorSinuosity.setStyleSheet('background-color: None')
        vlayer = self.vectorCombo.currentLayer()

        message, color = self.checkLayerAxes(vlayer)
        self.message(message,color,self.validatorSinuosity)

    def checkPolyLayer(self,lineLayer,polyLayer):
        message=''
        color=''

        if not polyLayer.isValid():
            message = polyLayer.name() + ' is not valid'
            color = 'red'
            self.validate_test = False
        else:
            self.validate_test = True
            message = polyLayer.name() + ' is valid'
            color = '#80ffd4'
        return message, color


    def checkLayerAxes(self, vlayer):
        message = ''
        color=''

        if not vlayer.isValid():
            message= vlayer.name()+' is not valid'
            color='red'
            self.validate_test=False

        elif vlayer.geometryType() != QgsWkbTypes.LineGeometry:
            message='your vector layer is not a Line'
            color='red'
            self.validate_test = False
        else:
            self.validate_test = True
            message = vlayer.name()+' is valid'
            color='#80ffd4'

        if vlayer.featureCount() > 1:
            message ='You have more then one feature on your vector layer'
            color = 'yellow'
            self.validate_test = False
        else:
            for feat in vlayer.getFeatures():
                the_geom = feat.geometry()
                len = the_geom.length()
                self.validate_test = True
                if self.stepSpin.value() >= the_geom.length():
                    message = ('Use a smaller value for step less than ' +
                                 str(round(len/1000,2)) + ' km')
                    color = 'yellow'
                    self.validate_test = False

        #TODO -- add validate CRS layer to be not a geographic
        crslayer=vlayer.crs().toProj4()
        if 'proj=longlat' in crslayer:
            self.validate_test = False
            message = 'The layer crs is not projected'
            color = 'yellow'
        if crslayer == '':
            self.validate_test = True
            message ='warning:the crs seems missing'
            color = 'yellow'
        return message,color

    def clearLayout(self,layout):
        '''
        clear layout function
        :return:
        '''
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def graph_data(self):

        step = self.stepSpin.value()
        shif = self.shiftSpin.value()

        if self.validate_test == None:
            self.message('You have to validate your layers first','yellow',self.validatorSinuosity)
        if self.validate_test == True:
            vlayer = self.vectorCombo.currentLayer()
            for feat in vlayer.getFeatures():
                the_geom = feat.geometry()
                x,y = sinuosity(the_geom,step ,shif)
                self.line = the_geom

            self.figure.clear()
            # create an axis
            self.ax = self.figure.add_subplot(111)
            self.ax.plot( x, y, 'b')
            self.Xcsv = x
            self.Ycsv = y


            #def addVline():
            #if breakButton.isChecked():
            #       figure.canvas.mpl_connect('button_press_event', OnClick)

            #TODO: debug
            #self.canvas.show()
            self.canvas.draw()
            #set variable graphState to true to remember graph is plotted
            self.graphicState =True

            self.writecsv()

            #self.graph.hide()

    def addBreaks(self):

        def OnClick(event):
            # ax=self.figure.add_subplot(111)
            # Ottieni le coordinate x e y del punto cliccato
            x_clicked = event.xdata
            y_clicked = event.ydata
            self.ax.axvline(int(x_clicked),linewidth=4, color='r')
            # Stampa le coordinate x e y
            print(f'Coordinate cliccate: x={x_clicked}, y={y_clicked}')
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

        vlayer = self.vectorCombo.currentLayer()
        for feat in vlayer.getFeatures():
            the_geom = feat.geometry()
        #TODO: remove the line for debugging
        #self.message(str(vlayer.name())+'|'+str(the_geom.length())+'|'+str(self.breaks), 'red')
        crsSinuosity = vlayer.crs()
        ll1 = createMemLayer(the_geom, self.breaks,crsSinuosity)
        QgsProject.instance().addMapLayer(ll1)

    def finalBraiding(self):
        vlayer = self.RiverLayerComboBox.currentLayer()
        for feat in vlayer.getFeatures():
            the_geom = feat.geometry()
        crsSinuosity = vlayer.crs()
        ll2 = createBradingLayer(the_geom, self.breaks1,self.X,self.Y, crsSinuosity)
        QgsProject.instance().addMapLayer(ll2)


    def graph_braiding(self):
        vlayer = self.layerXS
        channelLayer = self.channelLayerComboBox.currentLayer()
        step = self.stepSpinXS.value()
        win_size=self.braidingSpin.value()

        if vlayer.isValid():
            if self.XSgenerated:
                self.X,self.Y = bradingIndex(vlayer,channelLayer,step,win_size)

                self.figure1.clear()
                self.ax1 = self.figure1.add_subplot(111)
                self.ax1.plot(self.X, self.Y, 'b')
                # debug
                # print('out',X,Y,sep='-')
                self.canvas1.draw()

                # set variable graphState to true to remember graph is plotted
                self.graphicState = True


            else:
                self.message('Cross section missing','red',self.validatorBraiding)
        else:
            self.message('Cross section is invalid', 'red', self.validatorBraing)

    def addBreaks1(self):

        def OnClick(event1):
            # ax=self.figure.add_subplot(111)
            # Ottieni le coordinate x e y del punto cliccato
            x_clicked = event1.xdata
            y_clicked = event1.ydata
            self.ax1.axvline(int(x_clicked),linewidth=4, color='r')
            # Stampa le coordinate x e y
            print(f'Coordinate cliccate: x={x_clicked}, y={y_clicked}')
            self.canvas1.draw()
            self.breaks1.append(float(event1.xdata))

        if self.graphicState is True:
            if self.breakButton1.isChecked():
                self.breakButton1.setText('stop-break')
                self.cid1 = self.figure1.canvas.mpl_connect('button_press_event', OnClick)

            else:
                self.breakButton1.setText('Add Break')
                self.figure1.canvas.mpl_disconnect(self.cid1)
                self.finalBraiding()
                print('onClick', self.breaks1 )
                # ll1 = createMemLayer(self.line, self.breaks)
                # QgsMapLayerRegistry.instance().addMapLayers([ll1])
        else:
            self.message('You have to graph your data first','yellow', self.validatorBraing)


    def writeFile(self):
        fileName, __ = QFileDialog.getSaveFileName(self, 'Save CSV file',
                                               "", "CSV (*.csv);;All files (*)")
        fileName = os.path.splitext(str(fileName))[0] + '.csv'
        self.lineOutput.setText(fileName)

    def writecsv(self):
        self.filecsvtemp = tempfile.NamedTemporaryFile(mode="w",suffix='.csv')
        # filecsv = open(self.lineOutput.text(),'w')
        self.filecsvtemp.write('length,sinuosity\n')
        for row in range(len(self.Xcsv)):
            self.filecsvtemp.write(str(round(self.Xcsv[row],4))+','+str(round(self.Ycsv[row],4))+'\n')
        self.filecsvtemp.close()

        self.filecsvpath = os.path.splitext(str(self.filecsvtemp.name))[0] + '.csv'
        self.lineOutput.setText(self.filecsvpath)

    def do_clear_graph(self):
        #clear sinuosity graph
        self.figure.clear()
        self.canvas.draw()
        # clear all breaks
        self.breaks = []
    def do_clear_graph1(self):
        # clear graph brading
        self.figure1.clear()
        self.canvas1.draw()
        self.breaks1 = []



    def transect(self):
        step = self.stepSpinXS.value()
        XS_Len = self.sectionSpinXS.value()
        river_axes= self.RiverLayerComboBox.currentLayer()
        pt_mid, sections = create_XS_secs(river_axes,step=step,sez_length=XS_Len)
        QgsProject.instance().addMapLayer(sections)
        self.XSgenerated = True
        self.layerXS=sections