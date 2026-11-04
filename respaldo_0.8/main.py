from pathlib import Path
from typing import Annotated, Literal
import sqlite3
import json

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, StringConstraints

import motor

app = FastAPI(title='API de TecnoGUIA', version='0.7.1')
Texto = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class ContextoClase(BaseModel):
    conocimientos_previos: Annotated[str, StringConstraints(strip_whitespace=True, max_length=2000)] = ''
    modalidad: Literal['individual', 'parejas', 'grupos'] = 'grupos'
    dificultad: Literal['inicial', 'intermedia', 'avanzada'] = 'intermedia'


class SolicitudActividad(ContextoClase):
    grado: Literal[5, 6]
    contenido: str = Field(min_length=2)
    duracion_minutos: int = Field(gt=0)
    cantidad_alumnos: int = Field(gt=0)
    materiales: list[Texto] = Field(min_length=1)


@app.get('/')
def inicio():
    return {'proyecto': 'TecnoGUIA', 'mensaje': 'API conectada a SQLite'}


@app.get('/formulario', include_in_schema=False)
def formulario():
    archivo = Path(__file__).resolve().parent / 'formulario_multi.html'
    if not archivo.is_file():
        raise HTTPException(404, 'Falta formulario_multi.html en la carpeta del proyecto.')
    return FileResponse(archivo, media_type='text/html')


@app.post('/solicitudes')
def recibir(datos: SolicitudActividad):
    return {'mensaje': 'Solicitud recibida correctamente', 'datos': datos.model_dump()}


@app.get('/catalogo')
def catalogo(grado: Annotated[int | None, Query(ge=5,le=6)] = None):
    try:
        return motor.catalogo(grado)
    except sqlite3.Error as exc:
        raise HTTPException(503, 'No se pudo leer la base. Ejecutá crear_base.py y agregar_actividades.py.') from exc


@app.get('/proyectos')
def proyectos():
    try:
        con = motor.abrir_base()
        try:
            resultado = []
            tabla = 'proyectos_unicos_pdf' if con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='proyectos_unicos_pdf'").fetchone() else 'proyectos_pdf'
            for fila in con.execute(f'SELECT ficha_json, estado, contenido_id FROM {tabla} ORDER BY numero'):
                ficha = json.loads(fila['ficha_json'])
                ficha['estado'] = fila['estado']
                ficha['contenido_id'] = fila['contenido_id']
                resultado.append(ficha)
            return resultado
        finally:
            con.close()
    except sqlite3.Error as exc:
        raise HTTPException(503, 'Falta importar el catálogo. Ejecutá importar_unicos.py.') from exc


class SolicitudBusqueda(BaseModel):
    grado: Literal[5, 6]
    contenido_nap_id: Texto
    materiales: list[Texto] = Field(min_length=1)
    duracion_minutos: int = Field(gt=0)
    modalidad: Literal['individual', 'parejas', 'grupos'] = 'grupos'


@app.post('/actividades/buscar')
def buscar_actividades(datos: SolicitudBusqueda):
    try:
        return motor.buscar(datos.model_dump())
    except motor.PedidoNoDisponible as exc:
        raise HTTPException(422, exc.detalle) from exc
    except (sqlite3.Error, ValueError, KeyError) as exc:
        raise HTTPException(503, 'No se pudo consultar el catálogo y sus relaciones con los NAP.') from exc


@app.post('/actividades/generar')
def generar(datos: SolicitudActividad):
    try:
        return motor.generar(datos.model_dump())
    except motor.PedidoNoDisponible as exc:
        raise HTTPException(422, exc.detalle) from exc
    except (sqlite3.Error, ValueError, KeyError) as exc:
        raise HTTPException(503, 'No se pudo cargar la actividad. Revisá la base y su estructura.') from exc

@app.get('/curriculo')
def curriculo(grado: Annotated[int | None, Query(ge=5,le=6)] = None):
    try:
        with motor.abrir_base() as con:
            ejes=[dict(r) for r in con.execute('SELECT * FROM nap_ejes ORDER BY rowid')]
            contenidos=[json.loads(r['ficha_json']) for r in con.execute('SELECT * FROM nap_contenidos WHERE (? IS NULL OR grado=?) ORDER BY id',(grado,grado))]
            for contenido in contenidos:
                opciones=[]
                for r in con.execute('SELECT * FROM nap_vinculos WHERE contenido_id=?',(contenido['id'],)):
                    v=json.loads(r['ficha_json'])
                    tabla='actividades' if v['tipo']=='guia' else 'proyectos_unicos_pdf'
                    recurso=con.execute(f'SELECT * FROM {tabla} WHERE id=?',(v['recurso_id'],)).fetchone()
                    if recurso is None and v['tipo']=='guia' and con.execute("SELECT 1 FROM sqlite_master WHERE name='guias_nap'").fetchone():
                        recurso=con.execute('SELECT * FROM guias_nap WHERE id=?',(v['recurso_id'],)).fetchone()
                    if recurso is None:continue
                    v['titulo']=recurso['titulo']
                    if v['tipo']=='proyecto':v['proyecto']=json.loads(recurso['ficha_json'])
                    else:v['contenido_generador']=recurso['id']
                    opciones.append(v)
                contenido['actividades']=opciones
            return {'ejes':ejes,'contenidos':contenidos,'nota':'Relaciones didácticas propuestas; requieren revisión docente.'}
    except sqlite3.Error as exc:
        raise HTTPException(503,'Ejecutá asociar_nap.py para cargar los ejes y las relaciones.') from exc

# Las ediciones se guardan como propuestas nuevas, separadas del catálogo.
from datetime import datetime, timezone
from uuid import uuid4
from contextlib import contextmanager
from pydantic import model_validator


class EtapaEditable(BaseModel):
    nombre: Texto
    minutos: int = Field(gt=0, strict=True)
    acciones: list[Texto] = Field(min_length=1)


class GuiaEditable(BaseModel):
    model_config = {'extra': 'allow'}
    id: Texto
    titulo: Texto
    grado: Literal[5,6]
    duracion_minutos: int = Field(gt=0, strict=True)
    objetivos: list[Texto] = Field(min_length=1)
    preparacion_docente: list[Texto] = Field(min_length=1)
    materiales_por_grupo: list[Texto] = Field(min_length=1)
    consigna: Texto
    etapas: list[EtapaEditable] = Field(min_length=1)
    explicacion: Texto
    seguridad: list[Texto] = Field(min_length=1)
    evidencias: list[Texto] = Field(min_length=1)
    criterios_evaluacion: list[Texto] = Field(min_length=1)
    avisos: list[Texto] = Field(min_length=1)
    fuente: dict
    contexto_clase: ContextoClase | None = None

    @model_validator(mode='after')
    def comprobar_tiempos(self):
        if sum(e.minutos for e in self.etapas) != self.duracion_minutos:
            raise ValueError('Los minutos de las etapas deben sumar la duración total.')
        return self


@contextmanager
def conexion_guardado():
    if not motor.BASE.is_file():
        raise HTTPException(503,'Falta tecnoguia.db.')
    con=sqlite3.connect(motor.BASE)
    con.row_factory=sqlite3.Row
    try:
        with con:
            yield con
    finally:
        con.close()


@app.post('/propuestas', status_code=201)
def guardar_propuesta(guia: GuiaEditable):
    try:
        catalogo=motor.catalogo(guia.grado)
        if guia.id.startswith('IA-'):
            try:
                from uuid import UUID
                UUID(guia.id[3:])
                detalle=guia.model_dump()
                pedido=ia_generadora.PedidoGeneracion.model_validate(detalle.get('solicitud_generacion',{}))
                if pedido.grado != guia.grado or detalle.get('ia',{}).get('tipo') != 'generacion_completa':
                    raise ValueError('Origen de IA incoherente.')
                ficha=ia_generadora.recuperar(pedido.model_dump())
                if guia.fuente.get('contenido_id') != ficha['id']:
                    raise ValueError('Referencia curricular incoherente.')
            except (ValueError, motor.PedidoNoDisponible) as exc:
                raise HTTPException(422,'La propuesta generada no tiene un origen curricular válido.') from exc
        elif not any(a['id']==guia.id for a in catalogo):
            raise HTTPException(422,'La actividad de origen no pertenece al catálogo de ese grado.')
        identificador=str(uuid4())
        fecha=datetime.now(timezone.utc).isoformat()
        with conexion_guardado() as con:
            con.execute('INSERT INTO propuestas_guardadas VALUES (?,?,?,?,?)',
                (identificador,guia.titulo,guia.grado,fecha,json.dumps(guia.model_dump(),ensure_ascii=False)))
        return {'id':identificador,'titulo':guia.titulo,'creada_en':fecha}
    except sqlite3.Error as exc:
        raise HTTPException(503,'Ejecutá preparar_guardado.py para habilitar el guardado.') from exc


@app.get('/propuestas')
def listar_propuestas():
    try:
        with conexion_guardado() as con:
            return [dict(r) for r in con.execute('SELECT id,titulo,grado,creada_en FROM propuestas_guardadas ORDER BY creada_en DESC,id')]
    except sqlite3.Error as exc:
        raise HTTPException(503,'Ejecutá preparar_guardado.py para habilitar el guardado.') from exc


@app.get('/propuestas/{identificador}')
def recuperar_propuesta(identificador: str):
    try:
        with conexion_guardado() as con:
            r=con.execute('SELECT * FROM propuestas_guardadas WHERE id=?',(identificador,)).fetchone()
        if r is None:
            raise HTTPException(404,'No se encontró esa propuesta guardada.')
        return {'id':r['id'],'creada_en':r['creada_en'],'guia':json.loads(r['guia_json'])}
    except sqlite3.Error as exc:
        raise HTTPException(503,'Ejecutá preparar_guardado.py para habilitar el guardado.') from exc

import ia_local

class SolicitudIA(SolicitudActividad):
    contenido_nap_id: Annotated[str, StringConstraints(min_length=2,max_length=20)] | None = None

@app.get('/ia/estado')
def estado_ia():
    return ia_local.estado()

@app.post('/actividades/generar-ia')
def generar_ia(datos: SolicitudIA):
    try:
        return ia_local.adaptar(datos.model_dump(),datos.contenido_nap_id)
    except motor.PedidoNoDisponible as exc:
        raise HTTPException(422,exc.detalle) from exc
    except ia_local.ErrorIA as exc:
        raise HTTPException(exc.codigo,exc.mensaje) from exc
    except sqlite3.Error as exc:
        raise HTTPException(503,'No se pudo recuperar el contenido. Ejecutá asociar_nap.py y revisá la base.') from exc
    except (ValueError,KeyError) as exc:
        raise HTTPException(503,'La guía base no tiene la estructura esperada; revisá la base.') from exc

import ia_generadora

@app.get('/materiales')
def materiales_disponibles():
    return ia_generadora.catalogo_materiales()

@app.post('/actividades/crear-ia')
def crear_actividad_ia(datos: ia_generadora.PedidoGeneracion):
    try:
        return ia_generadora.generar(datos)
    except motor.PedidoNoDisponible as exc:
        raise HTTPException(422,exc.detalle) from exc
    except ia_local.ErrorIA as exc:
        raise HTTPException(exc.codigo,exc.mensaje) from exc
    except sqlite3.Error as exc:
        raise HTTPException(503,'No se pudo recuperar el contenido curricular. Revisá la base y asociar_nap.py.') from exc
