from django.core.management.base import BaseCommand, CommandError
from backend_integraciones.models import *

from django.db.models import Max

from backend_integraciones.api_mercado_publico import api_mercado_publico
from datetime import datetime

import time
import numpy as np
import pandas as pd

import json

import unidecode

class Command(BaseCommand):
    help = 'inserta licitaciones en el modelo relacional de la app'

    def add_arguments(self, parser):
        parser.add_argument('--historico', type=str, help='fecha para buscar licitaciones', )

    def handle(self, *args, **options):
        proceso_historico = options['historico']

        if proceso_historico:
            historico = True
        else:
            historico = False
        
        licitaciones_por_insertar = LicitacionRequest.objects.select_related('proceso').filter(
            esta_completa=True,
            esta_en_bd=False,
            proceso__historico=historico
        )

        proceso__id__max = licitaciones_por_insertar.aggregate(Max('proceso__id'))['proceso__id__max']

        licitaciones_por_insertar = licitaciones_por_insertar.filter(proceso__id=proceso__id__max)

        total_licitaciones = len(licitaciones_por_insertar)
        i = 0

        for licitacion_request in licitaciones_por_insertar:
            # self.stdout.write(str(licitaciones_por_insertar))
            json_licitacion = json.loads(licitacion_request.datos_json)
            licitacion_id = self.extractor(json_licitacion)
            
            licitacion_checklist = LicitacionChecklist(
                codigo = licitacion_request.codigo,
                licitacion_id = licitacion_id if licitacion_id > 0 else None,
                error = licitacion_id == -1
            )

            if licitacion_id > 0:
                self.stdout.write("INSERT licitacion codigo: {0}".format(licitacion_request.codigo))
            else:
                self.stdout.write("ERROR licitacion codigo: {0}".format(licitacion_request.codigo))

            licitacion_checklist.save()
            licitacion_request.esta_en_bd = True
            licitacion_request.save()

            i += 1

            self.stdout.write("### PROGRESS: {0}/{1} -> {2}".format(str(i), str(total_licitaciones), str((i*1.0)/total_licitaciones)))
        
    def extractor(self, json_licitacion):
        diccionario = self.generar_diccionario()
        licitacion_id = -1
        try:
            comprador = json_licitacion['Comprador']
            #agregar normalizador de strings!!!
            if not self.entidad_existe('organismo_codigo', comprador['CodigoOrganismo'], diccionario):
                organismo = Organismo(
                    codigo_origen = comprador['CodigoOrganismo'],
                    rut_organismo = '',
                    nombre = self.normalizar_texto(comprador['NombreOrganismo']),
                    cantidad_reclamos = json_licitacion['CantidadReclamos'],
                )

                organismo.save()

                organismo_id = organismo.id
                diccionario['organismo_codigo'][comprador['CodigoOrganismo']] = organismo_id
            else:
                organismo_id = diccionario['organismo_codigo'][comprador['CodigoOrganismo']]
            
            if not self.entidad_existe('region', self.normalizar_texto(comprador['RegionUnidad']), diccionario):
                region = Region(
                    nombre = self.normalizar_texto(comprador['RegionUnidad']),
                )

                region.save()

                region_id = region.id
                diccionario['region'][self.normalizar_texto(comprador['RegionUnidad'])] = region_id

            else:
                region_id = diccionario['region'][self.normalizar_texto(comprador['RegionUnidad'])]
            
            if not self.entidad_existe('comuna', self.normalizar_texto(comprador['ComunaUnidad']), diccionario):
                comuna = Comuna(
                    nombre = self.normalizar_texto(comprador['ComunaUnidad']),
                    region_id = region_id,
                )

                comuna.save()

                comuna_id = comuna.id
                diccionario['comuna'][self.normalizar_texto(comprador['ComunaUnidad'])] = comuna_id
            else:
                comuna_id = diccionario['comuna'][self.normalizar_texto(comprador['ComunaUnidad'])]

            if not self.entidad_existe('unidad', comprador['RutUnidad'], diccionario):
                unidad = UnidadOrganismo(
                    rut_unidad = comprador['RutUnidad'],
                    codigo_unidad = comprador['CodigoUnidad'],
                    nombre = self.normalizar_texto(comprador['NombreUnidad']),
                    organismo_id = organismo_id,
                    direccion = self.normalizar_texto(comprador['DireccionUnidad']),
                    comuna_id = comuna_id,
                )

                unidad.save()

                unidad_id = unidad.id
                diccionario['unidad'][comprador['RutUnidad']] = unidad_id

            else:
                unidad_id = diccionario['unidad'][comprador['RutUnidad']]
            
            if not self.entidad_existe('persona', comprador['RutUsuario'], diccionario):
                persona = Persona(
                    rut = comprador['RutUsuario'],
                    nombre = self.normalizar_texto(comprador['NombreUsuario']),
                    contacto = '',
                    codigo_origen = comprador['CodigoUsuario'],
                )

                persona.save()
                persona_id = persona.id
                diccionario['persona'][comprador['RutUsuario']] = persona_id
            else:
                persona_id = diccionario['persona'][comprador['RutUsuario']]

            if not self.entidad_existe('cargo', self.normalizar_texto(comprador['CargoUsuario']), diccionario):
                cargo = Cargo(
                    nombre = self.normalizar_texto(comprador['CargoUsuario']),
                )

                cargo.save()
                cargo_id = cargo.id
                diccionario['cargo'][self.normalizar_texto(comprador['CargoUsuario'])] = cargo_id
            else:
                cargo_id = diccionario['cargo'][self.normalizar_texto(comprador['CargoUsuario'])]
            
            persona_organismo = PersonaOrganismo(
                persona_id = persona_id,
                unidad_organismo_id = unidad_id,
                cargo_id = cargo_id,
                email = ''
            )

            persona_organismo.save()

        except Exception as e:
            self.stderr.write('###### Error en extraccion de Comprador')
            self.stderr.write(str(e))

        # Licitaciones
        try:
            if not self.entidad_existe('estado_licitacion', json_licitacion['CodigoEstado'], diccionario):
                estado_licitacion = EstadoLicitacion(
                    codigo_origen = json_licitacion['CodigoEstado'],
                    nombre = self.normalizar_texto(json_licitacion['Estado']),
                )

                estado_licitacion.save()
                estado_licitacion_id = estado_licitacion.id
                diccionario['estado_licitacion'][json_licitacion['CodigoEstado']] = estado_licitacion_id
            else:
                estado_licitacion_id = diccionario['estado_licitacion'][json_licitacion['CodigoEstado']]

            if not self.entidad_existe('tipo_licitacion', json_licitacion['CodigoTipo'], diccionario):
                tipo_licitacion = TipoLicitacion(
                    codigo_origen = json_licitacion['CodigoTipo'],
                    nombre = self.normalizar_texto(json_licitacion['Tipo']),
                )

                tipo_licitacion.save()
                tipo_licitacion_id = tipo_licitacion.id
                diccionario['tipo_licitacion'][json_licitacion['CodigoTipo']] = tipo_licitacion_id
            else:
                tipo_licitacion_id = diccionario['tipo_licitacion'][json_licitacion['CodigoTipo']]

            if not self.entidad_existe('licitacion', json_licitacion['CodigoExterno'], diccionario):
                licitacion = Licitacion(
                    codigo = json_licitacion['CodigoExterno'],
                    nombre = self.normalizar_texto(json_licitacion['Nombre']),
                    
                    estado_id = estado_licitacion_id,
                    tipo_id = tipo_licitacion_id,
                    
                    descripcion = self.normalizar_texto(json_licitacion['Descripcion']),
                    fecha_cierre = json_licitacion['FechaCierre'],
                    informada = json_licitacion['Informada'],
                    etapas = json_licitacion['Etapas'],
                    moneda = json_licitacion['Moneda'],

                    comprador = persona_organismo,

                    fecha_creacion = json_licitacion['Fechas']['FechaCreacion'],
                    fecha_inicio = json_licitacion['Fechas']['FechaInicio'],
                    fecha_final = json_licitacion['Fechas']['FechaFinal'],
                    fecha_pub_respuestas = json_licitacion['Fechas']['FechaPubRespuestas'],
                    fecha_acto_apertura_tecnica = json_licitacion['Fechas']['FechaActoAperturaTecnica'],
                    fecha_acto_apertura_economica = json_licitacion['Fechas']['FechaActoAperturaEconomica'],
                    fecha_publicacion = json_licitacion['Fechas']['FechaPublicacion'],
                    fecha_adjudicacion = json_licitacion['Fechas']['FechaAdjudicacion'],
                    fecha_estimada_adjudicacion = json_licitacion['Fechas']['FechaEstimadaAdjudicacion'],
                    fecha_soporte_fisico = json_licitacion['Fechas']['FechaSoporteFisico'],
                    fecha_tiempo_evaluacion = json_licitacion['Fechas']['FechaTiempoEvaluacion'],
                    fecha_estimada_firma = json_licitacion['Fechas']['FechaEstimadaFirma'],
                    fechas_usuario = json_licitacion['Fechas']['FechasUsuario'],
                    fecha_visita_terreno = json_licitacion['Fechas']['FechaVisitaTerreno'],
                    fecha_entrega_antecedentes = json_licitacion['Fechas']['FechaEntregaAntecedentes'],
                    url_acta_adjudicacion = json_licitacion['Adjudicacion']['UrlActa'] if json_licitacion['Adjudicacion'] is not None else None,
                )

                licitacion.save()
                licitacion_id = licitacion.id
                diccionario['licitacion'][json_licitacion['CodigoExterno']] = licitacion_id

        except Exception as e:
            self.stderr.write('###### Error en extraccion de Licitacion')
            self.stderr.write(str(e))
        
        # Items
        try:
            for item in json_licitacion['Items']['Listado']:
                if not self.entidad_existe('categoria_item', item['CodigoCategoria'], diccionario):
                    categoria_item = CategoriaItem(
                        codigo_origen = item['CodigoCategoria'],
                        nombre = self.normalizar_texto(item['Categoria']),
                    )

                    categoria_item.save()
                    categoria_item_id = categoria_item.id
                    diccionario['categoria_item'][item['CodigoCategoria']] = categoria_item_id
                else:
                    categoria_item_id = diccionario['categoria_item'][item['CodigoCategoria']]
                
                if not self.entidad_existe('item', item['CodigoProducto'], diccionario):
                    item_model = Item(
                        codigo_producto = item['CodigoProducto'],
                        nombre = self.normalizar_texto(item['NombreProducto']),
                        categoria_id = categoria_item_id,
                    )

                    item_model.save()
                    item_model_id = item_model.id
                    diccionario['item'][item['CodigoProducto']] = item_model_id
                else:
                    item_model_id = diccionario['item'][item['CodigoProducto']]
                
                if not self.entidad_existe('organismo_rut', item['Adjudicacion']['RutProveedor'], diccionario):
                    proveedor = Organismo(
                        codigo_origen = '',
                        rut_organismo = item['Adjudicacion']['RutProveedor'],
                        nombre = self.normalizar_texto(item['Adjudicacion']['NombreProveedor']),
                        cantidad_reclamos = 0,
                    )

                    proveedor.save()
                    proveedor_id = proveedor.id
                    diccionario['organismo_rut'][item['Adjudicacion']['RutProveedor']] = proveedor_id
                else:
                    proveedor_id = diccionario['organismo_rut'][item['Adjudicacion']['RutProveedor']]

                adjudicacion_item = AdjudicacionItem(
                    organismo_proveedor_id = proveedor_id,
                    cantidad = item['Adjudicacion']['Cantidad'],
                    monto_unitario = item['Adjudicacion']['MontoUnitario'],
                )

                adjudicacion_item.save()
                
                item_licitacion = ItemLicitacion(
                    item_id = item_model_id,
                    correlativo = item['Correlativo'],
                    unidad_medida = item['UnidadMedida'],
                    cantidad = item['Cantidad'],
                    adjudicacion = adjudicacion_item,
                    descripcion = self.normalizar_texto(item['Descripcion']),
                    licitacion_id = licitacion_id,
                )

                item_licitacion.save()

        except Exception as e:
            self.stderr.write('###### Error en extraccion de Items')
            self.stderr.write(str(e))
        return licitacion_id
    
    def entidad_existe(self, modelo, codigo, diccionario=None):
        if diccionario is None:
            diccionario = self.generar_diccionario()
        return codigo in diccionario[modelo].keys()

    def generar_diccionario(self):
        diccionario = {}

        config = {
            'comuna': ('nombre', Comuna),
            'region': ('nombre', Region),
            'persona': ('rut', Persona),
            'cargo': ('nombre', Cargo),
            'unidad': ('rut_unidad', UnidadOrganismo),
            'estado_licitacion': ('codigo_origen', EstadoLicitacion),
            'tipo_licitacion': ('codigo_origen', TipoLicitacion),
            'organismo_codigo': ('codigo_origen', Organismo),
            'organismo_rut': ('rut_organismo', Organismo),
            'item': ('codigo_producto', Item),
            'categoria_item': ('codigo_origen', CategoriaItem),
            'licitacion': ('codigo', Licitacion),
        }

        for llave_config, tupla_config in config.items():
            diccionario[llave_config] = {
                instancia[tupla_config[0]]: instancia['id'] for instancia in list(
                    tupla_config[1].objects.all().values('id', tupla_config[0])
                )
            }

        return diccionario

    def normalizar_texto(self, texto):
        return unidecode.unidecode(texto.upper().strip())
