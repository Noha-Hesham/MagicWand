from qgis.core import QgsProject, QgsRectangle, QgsVectorLayer, QgsFeature, QgsGeometry
import processing
import numpy as np

class PolygonMaker:
    def __init__(self, canvas, bin_index):
        self.bin_index = bin_index
        self.map_canvas = canvas

    def make_vector(self, point, buffer_multiply=1, torel_multiply=1, noise_multiply=10, single_mode=False):
        true_points = np.where(self.bin_index)
        func = lambda x, y, size: self.rect_geo(x, y, size)
        np_func = np.frompyfunc(func,3,1)
        size_multiply = self.map_canvas.width() / self.bin_index.shape[1]
        geos = np_func(true_points[1], true_points[0], size_multiply)

        unioned_feat = QgsFeature()
        unioned_feat.setGeometry(QgsGeometry().unaryUnion(geos))

        mem_layer = QgsVectorLayer('Polygon?crs=epsg:4326&field=MYNYM:integer&field=MYTXT:string', 'magic_wand', 'memory')
        mem_layer_provider = mem_layer.dataProvider()
        mem_layer_provider.addFeature(unioned_feat)
        
        single_part_layer = processing.run('qgis:multiparttosingleparts', {'INPUT':mem_layer,'OUTPUT':'memory:'})
        single_features = single_part_layer['OUTPUT'].getFeatures()
        
        output_features = []
        minimum_area = self.rect_geo(0,0, size_multiply).area()
        buffer_dist = self.map_canvas.mapUnitsPerPixel() * buffer_multiply * size_multiply
        torelance = self.map_canvas.mapUnitsPerPixel() * torel_multiply * size_multiply
        for feature in single_features:
            if single_mode and not feature.geometry().contains(self.map_canvas.getCoordinateTransform().toMapPoint(point.x(), point.y())):
                continue
            if feature.geometry().area() < minimum_area * noise_multiply:
                continue
            output_geo = feature.geometry().buffer(1 * buffer_dist, 1).buffer(-1 * buffer_dist, 2).simplify(torelance)
            output_feature = QgsFeature()
            output_feature.setGeometry(output_geo)
            output_features.append(output_feature)
        
        output_layer = QgsVectorLayer('Polygon?crs=epsg:4326&field=MYNYM:integer&field=MYTXT:string', 'magic_wand', 'memory')
        output_layer_provider = output_layer.dataProvider()
        output_layer_provider.addFeatures(output_features)
        
        QgsProject.instance().addMapLayer(output_layer)

    #make rectangle geometry by pointXY on Pixels
    def rect_geo(self, x, y, size_multiply):
        point1 = self.map_canvas.getCoordinateTransform().toMapPoint(x * size_multiply, y * size_multiply)
        point2 = self.map_canvas.getCoordinateTransform().toMapPoint((x + 1) * size_multiply, (y + 1) * size_multiply)

        geo = QgsGeometry.fromRect(QgsRectangle(point1.x(), point1.y(), point2.x(), point2.y()))
        return geo
