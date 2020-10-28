from django.conf import settings
from datetime import datetime
import requests
import json

class ApiMercadoPublico():
    # mover a los settings
    api_url = settings.API_MERCADO_PUBLICO_URL
    api_ticket = settings.API_MERCADO_PUBLICO_TICKET

    api_url_licitaciones_fecha = api_url + 'licitaciones.json?fecha={0}&ticket={1}'
    api_url_licitaciones_codigo = api_url + 'licitaciones.json?codigo={0}&ticket={1}'
    api_url_licitaciones_dia_actual = api_url + 'licitaciones.json?ticket={0}'

    #Retorna las licitaciones segun una fecha dada
    def get_licitaciones_por_fecha(self, fecha_inicio=None, fecha_fin=None):
        headers = {}

        if fecha_inicio is None:
            # fecha_inicio = datetime.now()
            fecha_inicio = datetime.strptime('02-02-2014', '%d-%m-%Y')
            print(fecha_inicio)

        return json.loads(
            requests.get(
                self.api_url_licitaciones_fecha.format(fecha_inicio.strftime(format='%d%m%Y'), self.api_ticket),
                headers=headers
            ).text
        )
    
    def get_licitacion_por_codigo(self, codigo_licitacion):
        headers = {}

        return json.loads(
            requests.get(
                self.api_url_licitaciones_codigo.format(str(codigo_licitacion), self.api_ticket),
                headers=headers
            ).text
        )

    def get_licitaciones_hoy(self):
        headers = {}

        return json.loads(
            requests.get(
                self.api_url_licitaciones_dia_actual.format(self.api_ticket),
                headers=headers
            ).text
        )
