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
        m.UpdateLicitacionesBuffer.objects.filter(codigo_licitacion=item['codigo_licitacion']).delete()
    
    def procesar_detalle_rut(self, item):
        rut_existe = m.RutContacto.objects.filter(rut=item['rut'])
        if len(rut_existe) > 0:
            rut_contacto = rut_existe[0]
        else:
            rut_contacto = m.RutContacto(rut=item['rut'])
        
        rut_contacto.encontrado = item['encontrado']

        for dato_contacto in item['datos_contacto']:
            if 'telefonos' in dato_contacto.keys():
                rut_contacto.telefonos = ', '.join(dato_contacto['telefonos'])
            if 'sitios_web' in dato_contacto.keys():
                rut_contacto.sitios_web = ', '.join(dato_contacto['sitios_web'])
            if 'contactos' in dato_contacto.keys():
                rut_contacto.contactos = dato_contacto['contactos']
        if type(item['datos_adicionales']).__name__ == 'dict':
            rut_contacto.nombre_completo = item['datos_adicionales']['nombre_completo']
            rut_contacto.rubro = item['datos_adicionales']['rubro']
            rut_contacto.subrubro = item['datos_adicionales']['subrubro']
            rut_contacto.actividad_economica = item['datos_adicionales']['actividad_economica']
            rut_contacto.comuna = item['datos_adicionales']['comuna']
            rut_contacto.region = item['datos_adicionales']['region']
            rut_contacto.fecha_inicio_empresa = item['datos_adicionales']['fecha_inicio']
            rut_contacto.tipo_contribuyente = item['datos_adicionales']['tipo_contribuyente']
            rut_contacto.subtipo_contribuyente = item['datos_adicionales']['subtipo_contribuyente']
        rut_contacto.save()

    def process_item(self, item, spider):
        if isinstance(item, dict):
            if item['tipo_item'] == 'licitacion_participante':
                self.procesar_licitacion_participante(item)
            elif item['tipo_item'] == 'licitacion_garantia':
                self.procesar_licitacion_garantia(item)
            elif item['tipo_item'] == 'detalle_rut':
                self.procesar_detalle_rut(item)
        return item
