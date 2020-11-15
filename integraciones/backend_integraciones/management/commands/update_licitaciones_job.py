from django.core.management.base import BaseCommand, CommandError
from backend_integraciones.models import *

from backend_integraciones.api_mercado_publico import api_mercado_publico
from datetime import datetime, timedelta

import time
import numpy as np
import pandas as pd

import json

import unidecode

class Command(BaseCommand):
    help = 'busca licitaciones que figuren como no adjudicadas y las actualiza'
    api = api_mercado_publico.ApiMercadoPublico()

    def add_arguments(self, parser):
        parser.add_argument('-f', '--fecha', type=str, help='fecha para buscar licitaciones', )
        parser.add_argument('--delta', type=str, help='numero de dias para hacer update de licitaciones', )
    
    def determinar_codigos_update(self, fecha_inicio=None, n=1000, delta=None):
        licitaciones_update = LicitacionRequest.objects.select_related('proceso').exclude(
            codigo_estado='8'
        )

        if fecha_inicio is not None:
            licitaciones_update = licitaciones_update.filter(
                proceso__fecha_licitaciones=fecha_inicio
            )
        
        if delta is None:
            delta = 30

        fechas_cierre = self.fechas_ultimo_mes(delta=delta)
        
        licitaciones_update = licitaciones_update.filter(
            fecha_cierre__in=fechas_cierre
        )

        # licitaciones_update = licitaciones_update.all()
        # licitaciones_update = licitaciones_update[:n]

        codigos = list(
            licitaciones_update.values_list('codigo', flat=True)
        )

        self.stdout.write("total: {0} y fechas:{1}".format(len(codigos), fechas_cierre))

        return (codigos, { l.codigo: l for l in licitaciones_update })
    
    def fechas_ultimo_mes(self, delta=30):
        d = datetime.today()
        return [(d - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(1, delta + 1)]

    def handle(self, *args, **options):
        # ayer = (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d")
        fecha_inicio = options['fecha'] if options['fecha'] else None
        delta = int(options['delta']) if options['delta'] else None

        codigos_buscar_en_api, licitaciones_update = self.determinar_codigos_update(delta=delta)

        if len(codigos_buscar_en_api) > 0:
            proceso = ProcesoExtraccion(
                fecha_licitaciones=fecha_inicio,
                message='update_licitaciones' 
            )
            proceso.save()

            total_licitaciones = len(codigos_buscar_en_api)

            licitaciones_bd_delete = []

            i = 0
            for codigo, licitacion_request in licitaciones_update.items():
                try:
                    time.sleep(2)
                    self.stdout.write("GET UPDATE licitacion codigo: {0}".format(codigo))

                    licitacion_completa = self.api.get_licitacion_por_codigo(codigo)
                    licitacion_completa = licitacion_completa['Listado'][0]
                    
                    codigo_estado_update = str(licitacion_completa['CodigoEstado'])

                    if codigo_estado_update == str(licitacion_request.codigo_estado):
                        self.stdout.write("NOTHING TO UPDATE licitacion codigo: {0}".format(codigo))
                    else:
                        licitacion_request.codigo_estado = codigo_estado_update,
                        licitacion_request.nombre = licitacion_completa['Nombre'],
                        licitacion_request.fecha_cierre = licitacion_completa['FechaCierre'],
                        licitacion_request.datos_json = json.dumps(licitacion_completa)
                        licitacion_request.esta_completa = True
                        licitacion_request.esta_en_bd = False
                        licitacion_request.proceso = proceso
                        licitacion_request.save()

                        self.stdout.write("SUCCESS UPDATE licitacion codigo: {0}".format(codigo))
                        licitaciones_bd_delete.append(codigo)

                except Exception as e:
                    self.stdout.write("ERROR licitacion codigo: {0}".format(codigo))
                    self.stderr.write(str(e))
                i += 1
                self.stdout.write("### PROGRESS: {0}/{1} -> {2}".format(str(i), str(total_licitaciones), str((i*1.0)/total_licitaciones)))
            
            proceso.status = "FINISHED"
            proceso.save()

            self.stdout.write("### DELETE LICITACIONES MODELO ")
            Licitacion.objects.filter(codigo__in=licitaciones_bd_delete).delete()
            for codigo_licitacion in licitaciones_bd_delete:
                UpdateLicitacionesBuffer(codigo_licitacion = codigo_licitacion).save()

            self.stdout.write("PROCESS FINISHED")
