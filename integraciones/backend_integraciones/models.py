from django.db import models

class Licitacion(models.Model):
    codigo = models.CharField(max_length=50, null=False, blank=False)
    nombre = models.CharField(max_length=250, null=True, blank=True)
    estado = models.ForeignKey("EstadoLicitacion", on_delete=models.CASCADE)
    descripcion = models.TextField()
    fecha_cierre = models.DateTimeField(null=True)
    comprador = models.ForeignKey("PersonaOrganismo", on_delete=models.CASCADE)
    tipo = models.ForeignKey("TipoLicitacion", on_delete=models.CASCADE)
    moneda = models.CharField(max_length=15, null=True, blank=True)
    etapas = models.IntegerField()

    informada = models.IntegerField(null=True)

    fecha_creacion = models.DateTimeField(null=True)
    fecha_inicio = models.DateTimeField(null=True)
    fecha_final = models.DateTimeField(null=True)
    fecha_pub_respuestas = models.DateTimeField(null=True)
    fecha_acto_apertura_tecnica = models.DateTimeField(null=True)
    fecha_acto_apertura_economica = models.DateTimeField(null=True)
    fecha_publicacion = models.DateTimeField(null=True)
    fecha_adjudicacion = models.DateTimeField(null=True)
    fecha_estimada_adjudicacion = models.DateTimeField(null=True)
    fecha_soporte_fisico = models.DateTimeField(null=True)
    fecha_tiempo_evaluacion = models.DateTimeField(null=True)
    fecha_estimada_firma = models.DateTimeField(null=True)
    fechas_usuario = models.DateTimeField(null=True)
    fecha_visita_terreno = models.DateTimeField(null=True)
    fecha_entrega_antecedentes = models.DateTimeField(null=True)

    url_acta_adjudicacion = models.CharField(max_length=250, null=True, blank=True)

    #agregar campos que faltan

    @property
    def dias_cierre(self):
        return 0

class EstadoLicitacion(models.Model):
    codigo_origen = models.IntegerField()
    nombre = models.CharField(max_length=50)

class TipoLicitacion(models.Model):
    codigo_origen = models.IntegerField()
    nombre = models.CharField(max_length=50)

class Organismo(models.Model):
    codigo_origen = models.CharField(max_length=30)
    rut_organismo = models.CharField(max_length=30)
    nombre = models.CharField(max_length=250)
    cantidad_reclamos = models.IntegerField()

class Persona(models.Model):
    rut = models.CharField(max_length=30)
    nombre = models.CharField(max_length=250)
    contacto = models.CharField(max_length=250, null=True, blank=True)
    codigo_origen = models.CharField(max_length=100)

class PersonaOrganismo(models.Model):
    persona = models.ForeignKey("Persona", on_delete=models.CASCADE)
    unidad_organismo = models.ForeignKey("UnidadOrganismo", on_delete=models.CASCADE)
    cargo = models.ForeignKey("Cargo", on_delete=models.CASCADE)
    email = models.CharField(max_length=250, null=True, blank=True)

class UnidadOrganismo(models.Model):
    rut_unidad = models.CharField(max_length=30)
    codigo_unidad = models.CharField(max_length=120)
    nombre = models.CharField(max_length=250)
    organismo = models.ForeignKey("Organismo", on_delete=models.CASCADE)
    direccion = models.CharField(max_length=250)
    comuna = models.ForeignKey("Comuna", on_delete=models.CASCADE)

class Comuna(models.Model):
    nombre = models.CharField(max_length=250)
    region = models.ForeignKey("Region", on_delete=models.CASCADE)

class Region(models.Model):
    nombre = models.CharField(max_length=250)

class Cargo(models.Model):
    nombre = models.CharField(max_length=250)

class ItemLicitacion(models.Model):
    item = models.ForeignKey("Item", on_delete=models.CASCADE)
    correlativo = models.IntegerField()
    unidad_medida = models.CharField(max_length=50)
    cantidad = models.FloatField()
    adjudicacion = models.ForeignKey("AdjudicacionItem", null=True, on_delete=models.CASCADE)
    descripcion = models.TextField()
    licitacion = models.ForeignKey("Licitacion", null=True, on_delete=models.CASCADE)

class Item(models.Model):
    codigo_producto = models.CharField(max_length=20)
    categoria = models.ForeignKey("CategoriaItem", null=True, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=250)

class CategoriaItem(models.Model):
    codigo_origen = models.CharField(max_length=20)
    nombre = models.CharField(max_length=250)

class AdjudicacionItem(models.Model):
    organismo_proveedor = models.ForeignKey("Organismo", on_delete=models.CASCADE)
    cantidad = models.FloatField()
    monto_unitario = models.FloatField()

class LicitacionRequest(models.Model):
    codigo = models.CharField(max_length=50, null=False, blank=False)
    nombre = models.CharField(max_length=250, null=True, blank=True)
    proceso = models.ForeignKey("ProcesoExtraccion", null=False, blank=False, on_delete=models.CASCADE)
    codigo_estado = models.CharField(max_length=50, null=True, blank=True)
    fecha_cierre = models.CharField(max_length=50, null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    datos_json = models.TextField(blank=True, default="")
    esta_completa = models.BooleanField(default=False)
    esta_en_bd = models.BooleanField(default=False)

class LicitacionChecklist(models.Model):
    codigo = models.CharField(max_length=50, null=False, blank=False)
    licitacion = models.ForeignKey("Licitacion", null=False, blank=False, on_delete=models.CASCADE)
    error = models.BooleanField(default=False)

class ProcesoExtraccion(models.Model):
    fecha_ejecucion = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, blank=True, default="")
    message = models.TextField(blank=True, default="")
    historico = models.BooleanField(default=False)
    fecha_licitaciones = models.CharField(max_length=50, null=True, blank=True, default="")

# se trae con Scrapy las garantias de una licitacion
class LicitacionScraping(models.Model):
    codigo_licitacion = models.CharField(max_length=50, null=False, blank=False)
    garantia_seriedad_exige = models.BooleanField(default=False)
    garantia_seriedad_monto = models.CharField(max_length=50, blank=True, default="")
    garantia_seriedad_glosa = models.TextField(blank=True, default="")
    garantia_seriedad_restitucion = models.TextField(blank=True, default="")
    garantia_seriedad_fecha_vencimiento = models.CharField(max_length=50, blank=True, default="")
    garantia_principal_titulo = models.CharField(max_length=50, blank=True, default="")
    garantia_principal_monto = models.CharField(max_length=50, blank=True, default="")
    garantia_principal_glosa = models.TextField(blank=True, default="")
    garantia_principal_restitucion = models.TextField(blank=True, default="")
    garantia_principal_fecha_vencimiento = models.CharField(max_length=50, blank=True, default="")
    exigencias = models.TextField(blank=True, default="")
    datos_json = models.TextField(blank=True, default="")

class LicitacionParticipante(models.Model):
    codigo_licitacion = models.CharField(max_length=50, null=False, blank=False)
    proveedor = models.ForeignKey("Organismo", null=False, blank=False, on_delete=models.CASCADE)
    nombre_oferta = models.TextField(blank=True, default="")
    total_oferta = models.CharField(max_length=100, null=True, blank=True)
    estado = models.CharField(max_length=100, null=True, blank=True)

class RutContacto(models.Model):
    rut = models.CharField(max_length=30)
    nombre_completo = models.TextField(blank=True, default="")
    telefonos = models.TextField(blank=True, default="")
    sitios_web = models.TextField(blank=True, default="")
    contactos = models.TextField(blank=True, default="")
    rubro = models.TextField(blank=True, default="")
    subrubro = models.TextField(blank=True, default="")
    actividad_economica = models.TextField(blank=True, default="")
    comuna = models.TextField(blank=True, default="")
    region = models.TextField(blank=True, default="")
    fecha_inicio_empresa = models.TextField(blank=True, default="")
    tipo_contribuyente = models.TextField(blank=True, default="")
    subtipo_contribuyente = models.TextField(blank=True, default="")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

class ExtraccionEnCurso(models.Model):
    fecha_extraccion = models.CharField(max_length=50, null=True, blank=True, default="")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    en_curso = models.BooleanField(default=False)
    get_licitaciones = models.BooleanField(default=False)
    get_scraping_garantias = models.BooleanField(default=False)

class UpdateLicitacionesBuffer(models.Model):
    # fecha_update = models.CharField(max_length=50, null=True, blank=True, default="")
    codigo_licitacion = models.CharField(max_length=50, null=False, blank=False)
