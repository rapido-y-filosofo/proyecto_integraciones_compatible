# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

from backend_integraciones import models as m
import json

class ScraperMercadoPublicoPipeline(object):

    def procesar_licitacion_participante(self, item):
        organismo_existe = m.Organismo.objects.filter(rut_organismo=item['rut_proveedor'])

        if len(organismo_existe) > 0:
            proveedor_id = organismo_existe[0].id
        else:
            proveedor = m.Organismo(
                codigo_origen = '',
                rut_organismo = item['rut_proveedor'],
                nombre = item['nombre_proveedor'],
                cantidad_reclamos = 0
            )
            proveedor.save()
            proveedor_id = proveedor.id
        
        licitacion_participante = m.LicitacionParticipante.objects.filter(codigo_licitacion=item['codigo_licitacion'])
        licitacion_participante = licitacion_participante.filter(proveedor_id=proveedor_id)
        
        if len(licitacion_participante) > 0:
            licitacion_participante = licitacion_participante[0]
        else:
            licitacion_participante = m.LicitacionParticipante()
        
        licitacion_participante.codigo_licitacion = item['codigo_licitacion'] if item['codigo_licitacion'] is not None else ''
        licitacion_participante.proveedor_id = proveedor_id
        licitacion_participante.nombre_oferta = item['nombre_oferta'] if item['nombre_oferta'] is not None else ''
        licitacion_participante.total_oferta = item['total_oferta'] if item['total_oferta'] is not None else ''
        licitacion_participante.estado = item['estado'] if item['estado'] is not None else ''

        licitacion_participante.save()

    def procesar_licitacion_garantia(self, item):

        garantia_seriedad_exige = False
        garantia_seriedad_monto = ''
        garantia_seriedad_glosa = ''
        garantia_seriedad_restitucion = ''
        garantia_seriedad_fecha_vencimiento = ''
        garantia_principal_titulo = ''
        garantia_principal_monto = ''
        garantia_principal_glosa = ''
        garantia_principal_restitucion = ''
        garantia_principal_fecha_vencimiento = ''
        
        for garantia in item['garantias']:
            if 'seriedad' in garantia['titulo_garantia'].lower():
                garantia_seriedad_exige = True
                garantia_seriedad_monto = garantia['monto'] + ' ' + garantia['monto_tipo_moneda']
                garantia_seriedad_glosa = garantia['glosa']
                garantia_seriedad_restitucion = garantia['restitucion']
                garantia_seriedad_fecha_vencimiento = garantia['fecha_vencimiento']
            
            garantia_principal_titulo = garantia['titulo_garantia'].lower()
            garantia_principal_monto = garantia['monto'] + ' ' + garantia['monto_tipo_moneda']
            garantia_principal_glosa = garantia['glosa']
            garantia_principal_restitucion = garantia['restitucion']
            garantia_principal_fecha_vencimiento = garantia['fecha_vencimiento']
        
        criterio_texto = ''
        for criterio in item['criterios']:
            criterio_texto += criterio['nombre'] + ' ' + criterio['ponderacion'] + '\n'

        licitacion_scraping = m.LicitacionScraping.objects.filter(codigo_licitacion=item['codigo_licitacion'])

        if len(licitacion_scraping) > 0:
            licitacion_scraping = licitacion_scraping[0]
        else:
            licitacion_scraping = m.LicitacionScraping()
        
        licitacion_scraping.codigo_licitacion = item['codigo_licitacion']
        licitacion_scraping.garantia_seriedad_exige = garantia_seriedad_exige
        licitacion_scraping.garantia_seriedad_monto = garantia_seriedad_monto
        licitacion_scraping.garantia_seriedad_glosa = garantia_seriedad_glosa
        licitacion_scraping.garantia_seriedad_restitucion = garantia_seriedad_restitucion
        licitacion_scraping.garantia_seriedad_fecha_vencimiento = garantia_seriedad_fecha_vencimiento
        licitacion_scraping.garantia_principal_titulo = garantia_principal_titulo
        licitacion_scraping.garantia_principal_monto = garantia_principal_monto
        licitacion_scraping.garantia_principal_glosa = garantia_principal_glosa
        licitacion_scraping.garantia_principal_restitucion = garantia_principal_restitucion
        licitacion_scraping.garantia_principal_fecha_vencimiento = garantia_principal_fecha_vencimiento
        licitacion_scraping.exigencias = criterio_texto
        licitacion_scraping.datos_json = json.dumps(item)

        licitacion_scraping.save()

    def process_item(self, item, spider):
        if isinstance(item, dict):
            if item['tipo_item'] == 'licitacion_participante':
                self.procesar_licitacion_participante(item)
            else:
                self.procesar_licitacion_garantia(item)
        return item
