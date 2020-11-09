# https://www.mercadopublico.cl/Procurement/Modules/RFB/DetailsAcquisition.aspx?idlicitacion=1028871-29-LR20

#id grvGarantias

import scrapy
from scraper_mercado_publico.items import LicitacionParticipanteItem
from backend_integraciones import models as m

class SpiderMercadoPublico(scrapy.Spider):
    name = 'spider_mercado_publico'
    base_url = 'https://www.mercadopublico.cl{0}'
    licitacion_url = '/Procurement/Modules/RFB/DetailsAcquisition.aspx?idlicitacion={0}'

    limit_n = 500
    fecha_inicio = '2019-12-31'

    def start_requests(self):
        # codigos_licitacion = [
        #     '1155-27-R120',
        #     '1069417-237-L120',
        #     '1078177-48-LE20',
        #     '1070620-65-LQ20',
        #     '4351-111-LE19',
        #     '1489-7-L120',
        # ]

        licitaciones = m.LicitacionRequest.objects.all()[:self.limit_n]
        codigos_licitacion = list(licitaciones.values_list('codigo', flat=True))

        for codigo in codigos_licitacion:
            url_licitacion = self.licitacion_url.format(codigo)
            url_licitacion = self.base_url.format(url_licitacion)
            yield scrapy.Request(url_licitacion, self.parse, meta={'codigo_licitacion': codigo})

    def parse(self, response):
        codigo_licitacion = response.xpath('//*[@id="lblNumLicitacion"]/text()').get()
        codigo_meta = response.meta.get('codigo_licitacion')

        if codigo_licitacion != codigo_meta:
            print('################ error en los codigos')

        cuadro_oferta = response.xpath('//input[contains(@class, "cuadroOferta")]')

        if len(cuadro_oferta) == 1:
            try:
                cuadro_oferta_url = cuadro_oferta.xpath('./@href').extract()[0]
                cuadro_oferta_url = cuadro_oferta_url.replace('OpeningFrame.aspx', 'SupplySummary.aspx')
                cuadro_oferta_url = self.base_url.format(cuadro_oferta_url)
                yield scrapy.Request(
                    cuadro_oferta_url,
                    callback=self.parseParticipantes,
                    meta={
                        'codigo_licitacion': codigo_licitacion
                    }
                )
            except Exception as e:
                print("#########")
                print("error en cuadro oferta")
                print(e)
                print("#########")

        # tabla_garantias = response.xpath('//*[@id="grvGarantias"]')
        # garantias = tabla_garantias.xpath('//*[contains(@id, "lblFicha8TituloTipoGarantia")]/tr')
        garantias = response.xpath('//*[@id="grvGarantias"]/tr')

        garantias_resultado = []

        for tr_garantia in garantias:
            # tabla_garantia = tr_garantia.xpath('.//table[contains(@class, "tabla_ficha")]')
            # etiquetas = tabla_garantia.xpath('.//span/@id').extract()
            # etiquetas = [ee.replace('grvGarantias_ctl03_', '').replace('grvGarantias_ctl02_', '').replace('lblFicha8', '').replace('Titulo', '') for ee in etiquetas]
            # print(etiquetas)
            # print("#######")
            g_titulo_garantia = tr_garantia.xpath('.//*[contains(@id, "lblFicha8TituloTipoGarantia")]/text()').get()
            g_beneficiario = tr_garantia.xpath('.//span[contains(@id, "lblFicha8Beneficiario")]/text()').get()
            g_fecha_vencimiento = tr_garantia.xpath('.//span[contains(@id, "lblFicha8FechaVencimiento")]/text()').get()
            g_monto = tr_garantia.xpath('.//span[contains(@id, "lblFicha8Monto")]/text()').get()
            g_monto_tipo_moneda = tr_garantia.xpath('.//span[contains(@id, "lblFicha8TipoMoneda")]/text()').get()
            g_descripcion = tr_garantia.xpath('.//span[contains(@id, "lblFicha8Descripcion")]/text()').get()
            g_glosa = tr_garantia.xpath('.//span[contains(@id, "lblFicha8Glosa")]/text()').get()
            g_restitucion = tr_garantia.xpath('.//span[contains(@id, "lblFicha8Restitucion")]/text()').get()

            garantias_resultado.append(
                {
                    'titulo_garantia': g_titulo_garantia,
                    'beneficiario': g_beneficiario,
                    'fecha_vencimiento': g_fecha_vencimiento,
                    'monto': g_monto,
                    'monto_tipo_moneda': g_monto_tipo_moneda,
                    'descripcion': g_descripcion,
                    'glosa': g_glosa,
                    'restitucion': g_restitucion,
                }
            )
        
        criterios = response.xpath('//*[@id="Ficha6"]').xpath('.//table//tr[td]')
        criterios_resultado = []

        for criterio in criterios:
            criterios_resultado.append(
                {
                    'nombre': criterio.xpath('.//span[contains(@id, "lblNombreCriterio")]/text()').get(),
                    'observaciones': criterio.xpath('.//span[contains(@id, "lblObservaciones")]/text()').get(),
                    'ponderacion': criterio.xpath('.//span[contains(@id, "lblPonderacion")]/text()').get(),
                }
            )
        
        item = {
            'tipo_item': 'licitacion_garantia',
            'codigo_licitacion': codigo_licitacion,
            'codigo_con_fue_llamada': codigo_meta,
            'garantias': garantias_resultado,
            'criterios': criterios_resultado,
        }

        # print(item)

        yield item


    def aux_selector_font_anidada(self, tr, palabra):
        selector_dato = './td//*[contains(@id, "{0}")]{1}/text()'

        dato = tr.xpath(selector_dato.format(palabra, "/font")).get()
        if dato is None:
            dato = tr.xpath(selector_dato.format(palabra, "")).get()
        return dato

    def parseParticipantes(self, response):
        codigo_licitacion = response.meta.get('codigo_licitacion')
        
        try:
            tabla = response.xpath('//table[@id="grdSupplies"]')
            filas = tabla.xpath('./tr[contains(@class, "ItemStyle")]')
            
            for tr in filas:
                rut_proveedor = self.aux_selector_font_anidada(tr, "GvLblRutProvider")
                nombre_proveedor = self.aux_selector_font_anidada(tr, "GvLblProvider")
                nombre_oferta = self.aux_selector_font_anidada(tr, "GvLblSuppliesName")
                total_oferta = self.aux_selector_font_anidada(tr, "TotalOferta")
                estado = self.aux_selector_font_anidada(tr, "Estado")

                item = {
                    'tipo_item': 'licitacion_participante',
                    'codigo_licitacion': codigo_licitacion,
                    'rut_proveedor': rut_proveedor,
                    'nombre_proveedor': nombre_proveedor,
                    'nombre_oferta': nombre_oferta,
                    'total_oferta': total_oferta,
                    'estado': estado,
                }

                if rut_proveedor is not None:
                    yield item
                else:
                    print("###################")
                    print("rut vacio")
                    print("url: {0}".format(response.url))
                    print(item)
                    print("###################")
                
        except Exception as e:
            print(e)
            print('############### error en parseParticipantes')