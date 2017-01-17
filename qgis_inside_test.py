vlayer = QgsVectorLayer('/home/pierluigi/UNIVERSITA/frane_alveo_regione/pianure/elementi_morfo/topino/asse_alveo_topino.shp', 'asse_fiume', 'ogr')
f = open('/tmp/workfile.csv', 'w')
#QgsMapLayerRegistry.instance().addMapLayer(vlayer)
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