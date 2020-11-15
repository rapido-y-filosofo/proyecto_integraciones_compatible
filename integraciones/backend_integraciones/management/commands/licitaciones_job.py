from django.core.management.base import BaseCommand, CommandError
from backend_integraciones.models import *

from backend_integraciones.api_mercado_publico import api_mercado_publico
from datetime import datetime, timedelta

import time
import numpy as np
import pandas as pd
import json
import unidecode
import os.path

from django.core import management

class Command(BaseCommand):
    help = 'realiza requests a la API de Mercado Publico'
    api = api_mercado_publico.ApiMercadoPublico()

    def add_arguments(self, parser):
        parser.add_argument('-f', '--fecha', type=str, help='fecha para buscar licitaciones', )

    def handle(self, *args, **options):
        ayer = (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d")

        #revisar si las licitaciones de ayer se encuentran disponibles
        ##si estan disponibles, tomar la ultima fecha y ejecutar get_licitaciones_job
        ##si no, ejecutar get_licitaciones_job con el dia de ayer
        #ejecutar update_licitaciones_job con la fecha de ayer (las que cerraron ayer)
        #ejecutar etl_licitaciones_job con la fecha utilizada por get_licitaciones_job y por update
        #ejecutar scraper_mercado_publico con la fecha utilizada
        #ejecutar scraper_genealog con los organismos relacionados con las licitaciones extraidas

        try:
            log_file_path = 'log_commands.txt'
            if os.path.isfile(log_file_path):
                f = open(log_file_path, 'r+')
            else:
                f = open(log_file_path, 'w')
            
            proceso_extraccion_ayer = ProcesoExtraccion.objects.filter(
                fecha_licitaciones=ayer
            )

            if len(proceso_extraccion_ayer) > 0:
                self.stdout.write("[GET] LICITACIONES HISTORICAS")
                management.call_command('get_licitaciones_job', auto_fill='auto', stdout=f)
            else:
                self.stdout.write("[GET] LICITACIONES AYER")
                management.call_command('get_licitaciones_job', fecha=ayer, stdout=f)
            
            self.stdout.write("[GET] LICITACIONES EXITOSO")
            self.stdout.write("[INSERT] LICITACIONES")
            management.call_command('etl_licitaciones_job', todas='todas', stdout=f)
            self.stdout.write("[INSERT] LICITACIONES EXITOSO")
            ##scraper 1 se llama desde el CRON
            ##scraper 2 se llama desde el CRON
            f.close()

        except Exception as e:
            self.stdout.write("ERROR en la extraccion")
            self.stderr.write(str(e))

        self.stdout.write("PROCESO MERCADO PUBLICO COMPLETO")
