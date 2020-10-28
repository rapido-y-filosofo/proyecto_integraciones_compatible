from django.core.management.base import BaseCommand, CommandError
from backend_integraciones.models import *

from backend_integraciones.api_mercado_publico import api_mercado_publico
from datetime import datetime

import time
import numpy as np
import pandas as pd

import json

import unidecode

class Command(BaseCommand):
    help = 'realiza requests a la API de Mercado Publico'
    api = api_mercado_publico.ApiMercadoPublico()

    def add_arguments(self, parser):
        parser.add_argument('-f', '--fecha', type=str, help='fecha para buscar licitaciones', )
    
    def determinar_codigos_nuevos(self):
        d = datetime.today().strftime("%Y-%m-%d")
        licitaciones_hoy = LicitacionRequest.objects.select_related('proceso').filter(
            proceso__fecha_ejecucion__gte = d
        )

        codigos = list(
            licitaciones_hoy.values_list('codigo', flat=True)
        )

        licitaciones_hoy_api = self.api.get_licitaciones_hoy()
        licitaciones_nuevas = { l['CodigoExterno']: l for l in licitaciones_hoy_api['Listado'] }
        codigos_buscar_en_api = np.setdiff1d(list(licitaciones_nuevas.keys()), codigos)
        return (codigos_buscar_en_api, licitaciones_nuevas)
    
    def determinar_codigos_por_fecha(self, fecha_inicio='18-10-2019'):
        licitaciones = self.api.get_licitaciones_por_fecha(
            fecha_inicio = datetime.strptime(fecha_inicio, '%d-%m-%Y')
        )

        licitaciones_buscar_en_api = {}
        codigos_buscar_en_api = []

        for licitacion_json in licitaciones['Listado']:
            codigo = licitacion_json['CodigoExterno']
            licitaciones_buscar_en_api[codigo] = licitacion_json
            codigos_buscar_en_api.append(codigo)

        return (codigos_buscar_en_api, licitaciones_buscar_en_api)

    def handle(self, *args, **options):
        fecha_inicio = options['fecha']

        if fecha_inicio:
            codigos_buscar_en_api, licitaciones_nuevas = self.determinar_codigos_por_fecha(fecha_inicio)
            proceso_es_historico = True
        else:
            codigos_buscar_en_api, licitaciones_nuevas = self.determinar_codigos_nuevos()
            proceso_es_historico = False
            fecha_inicio = datetime.today().strftime("%Y-%m-%d")

        if len(codigos_buscar_en_api) > 0:
            proceso = ProcesoExtraccion(historico=proceso_es_historico, fecha_licitaciones=fecha_inicio)
            proceso.save()

            licitaciones_completas = {}
            
            total_licitaciones = 0

            for codigo in codigos_buscar_en_api:
                licitacion = licitaciones_nuevas[codigo]
                licitacion_request = LicitacionRequest(
                    codigo = codigo,
                    nombre = licitacion['Nombre'],
                    codigo_estado = licitacion['CodigoEstado'],
                    fecha_cierre = licitacion['FechaCierre'],
                    proceso = proceso,
                )
                licitacion_request.save()
                licitaciones_completas[codigo] = licitacion_request
                total_licitaciones += 1
            
            i = 0
            for codigo, licitacion_request in licitaciones_completas.items():
                try:
                    time.sleep(2)
                    self.stdout.write("GET licitacion codigo: {0}".format(codigo))

                    licitacion_completa = self.api.get_licitacion_por_codigo(codigo)
                    licitacion_completa = licitacion_completa['Listado'][0]

                    self.stdout.write("SUCCESS licitacion codigo: {0}".format(codigo))
                    
                    licitacion_request.datos_json = json.dumps(licitacion_completa)
                    licitacion_request.esta_completa = True

                    licitacion_request.save()

                except Exception as e:
                    self.stdout.write("ERROR licitacion codigo: {0}".format(codigo))
                    self.stderr.write(str(e))
                i += 1
                self.stdout.write("### PROGRESS: {0}/{1} -> {2}".format(str(i), str(total_licitaciones), str((i*1.0)/total_licitaciones)))
            
            proceso.status = "FINISHED"
            proceso.save()
            self.stdout.write("PROCESS FINISHED")
