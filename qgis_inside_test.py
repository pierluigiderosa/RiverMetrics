vlayer = QgsVectorLayer('/home/pierluigi/UNIVERSITA/frane_alveo_regione/pianure/elementi_morfo/topino/asse_alveo_topino.shp', 'asse_fiume', 'ogr')
f = open('/tmp/workfile.csv', 'w')
#QgsMapLayerRegistry.instance().addMapLayer(vlayer)
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
    output=[]

    while endStation <= riverLeng:
        startPoint = pointAtDist(geom,initStation)
        endPoint = pointAtDist(geom,endStation)
        distance = qgisdist(startPoint,endPoint)
        sinuosity = step/distance
        output.append([midStation,sinuosity])
        f.write(str(midStation)+','+'dist: '+str(distance)+'sin: '+str(sinuosity)+'\n')
        initStation += shift
        endStation += shift
        midStation += shift
        
for feat in vlayer.getFeatures():
    # do something with the feature
    the_geom = feat.geometry()
    sinuosity(the_geom,5000,500)
    
    
vfeat=vlayer.selectedFeatures()[0]
line=vfeat.geometry()

punto10mila=line.interpolate(10000)
punto20mila=line.interpolate(20000)

def splitLine(line,ptInit,ptEnd):
    puntoInit = ptInit.asPoint()
    puntoEnd = ptEnd.asPoint()
    sqrDistInit, minDistPointInit, afterVertexInit  = line.closestSegmentWithContext(puntoInit)
    sqrDistEnd, minDistPointEnd, afterVertexEnd  = line.closestSegmentWithContext(puntoEnd)
    #afterVertexEnd -=1
    pline = line.asPolyline()
    newPoints = []
    newPoints.append(minDistPointInit)
    for iter in range(afterVertexInit,afterVertexEnd):
        newPoints.append(pline[iter])
    newPoints.append(minDistPointEnd)
    #metto tutto in featire
    reach =  QgsVectorLayer('LineString', 'line' , "memory")
    pr = reach.dataProvider() 
    reachFeat = QgsFeature()
    reachFeat.setGeometry(QgsGeometry.fromPolyline(newPoints))
    pr.addFeatures([reachFeat])
    reach.updateExtents()
    QgsMapLayerRegistry.instance().addMapLayers([reach])
    
    
def plottapunto(punto):
    vl = QgsVectorLayer("Point", "temporary_points", "memory")
    pr = vl.dataProvider()
    # add fields
    pr.addAttributes([QgsField("name", QVariant.String)])
    vl.updateFields() # tell the vector layer to fetch changes from the provider
    # add a feature
    fet = QgsFeature()
    fet.setGeometry(punto)
    fet.setAttributes(["Johny"])
    pr.addFeatures([fet])
    # update layer's extent when new features have been added
    # because change of extent in provider is not propagated to the layer
    vl.updateExtents()
    QgsMapLayerRegistry.instance().addMapLayer(vl)

plottapunto(punto10mila)

