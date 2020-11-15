import scrapy
from scrapy.http import FormRequest
from scrapy.http import HtmlResponse

from backend_integraciones import models as m

import re
import json
import base64

class SpiderGenealog(scrapy.Spider):
    name = 'spider_genealog'
    base_url = 'https://www.genealog.cl/Geneanexus{0}'
    search_url = base_url.format('/search')
    detalle_url = '/{0}/CHILE/{1}/{2}/{3}-{4}'
    limit_n = 1000

    def start_requests(self):
        # ruts_buscar = [
        #     '79.715.730-9',
        #     '77.796.890-4',
        #     '10.453.263-2'
        # ]
        proveedores_scraping = set(m.RutContacto.objects.all().values_list('rut', flat=True))
        organismos = set(m.Organismo.objects.exclude(rut_organismo='').values_list('rut_organismo', flat=True))

        ruts_buscar = list(organismos.difference(proveedores_scraping))[:self.limit_n]

        # for rut in [ruts_buscar[0]]:
        for rut in ruts_buscar:
            formdata = {
                'value': rut,
                # 'ab': False,
                # 'filter': {'personas': True,
                #     'empresas': True,
                #     'lugares': False,
                #     'chile': True,
                #     'argentina': False,
                #     'bolivia': False,
                #     'colombia': False,
                #     'guatemala': False,
                #     'mexico': False,
                #     'venezuela': False
                # }
            }
            # print(self.search_url)
            yield FormRequest(self.search_url, self.parse, formdata=formdata, meta={'rut': rut})

    def parse(self, response):
        texto_script = response.xpath('//script[contains(text(), "var result")]/text()').get()
        texto_resultado_busqueda = re.search(r'var result\s*=\s*(.*?);', texto_script).group(1)
        resultado_busqueda = json.loads(texto_resultado_busqueda)

        if resultado_busqueda['matches'] == 1:
            rut_regex = resultado_busqueda['regex'].upper()
            resultado = resultado_busqueda['content'][rut_regex]
            nombre_completo = resultado['nombre_completo']
            codigo = resultado['code']
            nombre_completo = nombre_completo.upper().replace('.', '').strip().replace(' ', '-')
            empresa_o_persona = 'empresa'
            # detalle_url = '/{0}/CHILE/{1}/{2}/{3}-{4}'
            datos_adicionales = {
                'rut': response.meta.get('rut'),
                'nombre_completo': nombre_completo,
                'rubro': resultado['rubro'] if 'rubro' in resultado.keys() else '',
                'subrubro': resultado['subrubro'] if 'subrubro' in resultado.keys() else '',
                'actividad_economica': resultado['actividad_economica'] if 'actividad_economica' in resultado.keys() else '',
                'comuna': resultado['comuna'] if 'comuna' in resultado.keys() else '',
                'region': resultado['region'] if 'region' in resultado.keys() else '',
                'fecha_inicio': resultado['fecha_inicio'] if 'fecha_inicio' in resultado.keys() else '',
                'tipo_contribuyente': resultado['tipo_contribuyente'] if 'tipo_contribuyente' in resultado.keys() else '',
                'subtipo_contribuyente': resultado['subtipo_contribuyente'] if 'subtipo_contribuyente' in resultado.keys() else '',
            }

            url = self.detalle_url.format(
                empresa_o_persona,
                codigo,
                'nombre-y-rut',
                nombre_completo,
                rut_regex
            )

            url = self.base_url.format(url)
            yield scrapy.Request(url, self.parse_detalle, meta={
                'rut': datos_adicionales['rut'],
                'datos_adicionales': datos_adicionales
            })

        elif resultado_busqueda['matches'] == 0:
            yield {
                'tipo_item': 'detalle_rut',
                'rut': response.meta.get('rut'),
                'encontrado': False,
                'datos_contacto': [],
                'datos_adicionales': []
            }
    
    def aux_tr_parse(self, tr):
        td_parse = tr.xpath('.//td[contains(@class, "parseOnAsk")]/text()').get()
        td = base64.b64decode(td_parse)
        td_html = HtmlResponse(url='', body=td, encoding='utf-8')

        #telefonos
        if tr.xpath('.//td[contains(@class, "telefonos")]').get() is not None:
            telefonos = td_html.xpath('.//div[contains(@class, "telefono")]/input[contains(@id, "telefono")]/@value').extract()
            return { 'telefonos': [ str(telefono) for telefono in telefonos ] }
        #sitios web
        elif tr.xpath('.//td[contains(@class, "urls")]').get() is not None:
            sitios = td_html.xpath('.//div[contains(@class, "url")]/a/@href').extract()
            return { 'sitios_web': [ str(sitio) for sitio in sitios ] }
        #contactos
        elif tr.xpath('.//td[contains(text(), "Contacto")]').get() is not None:
            contactos = td.decode('utf-8').replace('<span>', ' ').replace('</span>', ' ').replace('<br>', ' ')
            contactos = re.sub(r"<a.*href.*</a>", "", contactos)
            contactos = contactos.strip()
            resultado = {
                'contactos': contactos
            }
            if td_html.xpath('.//a[contains(text(), "@")]').get() is not None:
                emails = td_html.xpath('.//a/text()').extract()
                resultado['emails'] = emails
            return resultado
        return {'otros': td.decode('utf-8')}

    def parse_detalle(self, response):
        tr_ocultos = response.xpath('//tr[@class="showOnAskTr"]')
        # print(len(tr_ocultos))
        item_rut = {
            'tipo_item': 'detalle_rut',
            'rut': response.meta.get('rut'),
            'encontrado': True,
            'datos_contacto': [],
            'datos_adicionales': response.meta.get('datos_adicionales')
        }
        for tr in tr_ocultos:
            item_rut['datos_contacto'].append(self.aux_tr_parse(tr))

        yield item_rut
