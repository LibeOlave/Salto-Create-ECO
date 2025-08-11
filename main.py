import pandas as pd
import requests
from html import unescape
from constants import BASE_URL, HEADERS, SSL
from functions import *
import sys
from fastapi import FastAPI
from pydantic import BaseModel
from threading import Thread

app = FastAPI()


class Referencia(BaseModel):
    ref: str
    name: str

class CircuitosELECT(BaseModel):
    name: str
    loop: int

# Formulario
class InputData(BaseModel):
    # General settings
    title : str
    prefix : str
    fase_comienzo : int
    documentacion: bool
    embalaje : bool
    etiqueta : bool
    pauta_montaje : bool
    util_montaje : bool
    patentes_afectados : bool
    ensayos : bool
    preserie : bool
    BETAs : bool

    # Electrical settings
    circuitos_simp : list[CircuitosELECT]
    circuitos_comp : list[CircuitosELECT]
        # añadir iteraciones
    utiles_test_cambio_mec : bool
    utiles_test_cambio_SW : bool
    cert_elect : bool
    ESD : bool
    FW : bool

    # Mecanical settings
    ref : list[Referencia]
    cert_mec : bool
    elctromec : bool

@app.get("/")
def print_message():
    return {'mensaje': 'API funcionando'}

@app.post("/create_ECO")
def create_ECO(form: InputData):
    
    # Inicializar las variables fijas
    ECO_blueprint_id = 'IEAEGZ4IOFSV2TKR'
    ECOs_para_crear_id = 'IEAEGZ4II5TNC7HH'
    eco_tag = 'IEAEGZ4IJUAIVNFQ'

    # Paso 1: copiar el proyecto principal
    data = copy_blueprint_folder(ECO_blueprint_id, ECOs_para_crear_id, form.title, form.prefix)
    main_folder_id = data['data'][0]['id']

    # Procesamiento en segundo plano
    def procesamiento():
        # Paso 2: eliminar las etapas que no se usen
        data = get_folder(main_folder_id)
        childIds = data['data'][0]['childIds']
        n = form.fase_comienzo
        numeros = [1,2,3,4]
        menores = [x for x in numeros if x < n]
        for child_id in childIds:
            folderData = get_folders(child_id)
            taskData = get_tasks(child_id)
            folder_title = folderData['data'][0]['title']
            if any(f'P{x}' in folder_title for x in menores):
                for folder in folderData['data']:
                    customFields = get_folder(folder['id'])['data'][0]['customFields']            
                    campo = next((f for f in customFields if f['id'] == eco_tag), None)
                    if campo is None or campo.get('value') != '[\"MANTENER SIEMPRE\"]':
                        delete_folder(folder['id'])

                for task in taskData['data']:
                    customFields = get_task(task['id'])['data'][0]['customFields']            
                    campo = next((f for f in customFields if f['id'] == eco_tag), None)
                    if campo is None or campo.get('value') != '[\"MANTENER SIEMPRE\"]':
                        task['campo_filtrado'] = campo
                        delete_task(task['id'])


        # Paso 3: Borrar tareas si su campo es false
        tasks = get_tasks(main_folder_id)

        for task in tasks['data']:
            customFields = get_task(task['id'])['data'][0]['customFields']
            campo = next((f for f in customFields if f['id'] == eco_tag), None)
            if campo is None:
                continue

            valores = json.loads(campo['value'])

            # Booleanos
            if "documentacion" in valores:
                if form.documentacion == False:
                    delete_task(task['id'])
            elif "embalaje" in valores and "etiqueta" in valores:
                if form.embalaje == False and form.etiqueta == False:
                    delete_task(task['id'])
            elif "embalaje" in valores:
                if form.embalaje == False:
                    delete_task(task['id'])
            elif "etiqueta" in valores:
                if form.etiqueta == False:
                    delete_task(task['id'])
            elif "pauta montaje" in valores:
                if form.pauta_montaje == False:
                    delete_task(task['id'])
            elif "util montaje" in valores:
                if form.util_montaje == False:
                    delete_task(task['id'])
            elif "patntes afectados" in valores:
                if form.patentes_afectados == False:
                    delete_task(task['id'])
            elif "ensayos" in valores:
                if form.ensayos == False:
                    delete_task(task['id'])
            elif "preserie" in valores:
                if form.preserie == False:
                    delete_task(task['id'])
            elif "BETAs" in valores:
                if form.BETAs == False:
                    delete_task(task['id'])
            elif "utiles test cambio mec" in valores and "utiles test cambio SW" in valores:
                if form.utiles_test_cambio_mec == False and form.utiles_test_cambio_SW == False:
                    delete_task(task['id'])
            elif "utiles test cambio mec" in valores:
                if form.utiles_test_cambio_mec == False:
                    delete_task(task['id'])
            elif "utiles test cambio SW" in valores:
                if form.utiles_test_cambio_SW == False:
                    delete_task(task['id'])
            elif "cert elect" in valores:
                if form.cert_elect == False:
                    delete_task(task['id'])
            elif "ESD" in valores:
                if form.ESD == False:
                    delete_task(task['id'])
            elif "FW" in valores:
                if form.FW == False:
                    delete_task(task['id'])
            elif "cert mec" in valores:
                if form.cert_mec == False:
                    delete_task(task['id'])
            elif "electromec" in valores:
                if form.elctromec == False:
                    delete_task(task['id'])
            # Circuitos electronicos
            elif "circuitos electronicos" in valores:
                if len(form.circuitos_simp) == 0 and len(form.circuitos_comp) == 0:
                    delete_task(task['id'])
            elif "circuito simple" in valores:
                if len(form.circuitos_simp) == 0:
                    delete_task(task['id'])
                else:
                    raw_title = task['title']
                    params['title'] = f'{raw_title.replace("<CircuitName>", form.circuitos_simp[0].name)} (1º loop)'
                    parentId = get_task(task['id'])['data'][0]['parentIds']
                    update_task(task['id'], params)
                    for j in range(form.circuitos_simp[0].loop - 1):
                        new_title = f'{raw_title.replace("<CircuitName>", form.circuitos_simp[0].name)} ({j + 2}º loop)'
                        copy_task(task['id'], parentId[0], new_title, '')

                    for i in range(len(form.circuitos_simp) - 1):
                        for j in range(form.circuitos_simp[i + 1].loop):
                            new_title = f'{raw_title.replace("<CircuitName>", form.circuitos_simp[i + 1].name)} ({j + 1}º loop)'
                            copy_task(task['id'], parentId[0], new_title, '')

            elif "circuito complex" in valores:
                if len(form.circuitos_comp) == 0:
                    delete_task(task['id'])
                else:
                    raw_title = task['title']
                    params['title'] = f'{raw_title.replace("<CircuitName>", form.circuitos_comp[0])} (1º loop)'
                    parentId = get_task(task['id'])['data'][0]['parentIds']
                    update_task(task['id'], params)
                    for j in range(form.circuitos_comp[0].loop - 1):
                        new_title = f'{raw_title.replace("<CircuitName>", form.circuitos_comp[0].name)} ({j + 2}º loop)'
                        copy_task(task['id'], parentId[0], new_title, '')

                    for i in range(len(form.circuitos_comp) - 1):
                        for j in range(form.circuitos_comp[i + 1].loop):
                            new_title = f'{raw_title.replace("<CircuitName>", form.circuitos_comp[i + 1].name)} ({j + 1}º loop)'
                            copy_task(task['id'], parentId[0], new_title, '')

            # Piezas mecanicas
            elif "ref piezas mec afectadas" in valores:
                if len(form.ref) == 0:
                    delete_task(task['id'])
                else:
                    more_info_task = get_task(task['id'])
                    raw_title = task['title']
                    new_title = raw_title.replace("Part ref.", form.ref[0].ref).replace("Part name", form.ref[0].name)
                    params = {
                        'title': new_title
                    }
                    update_task(task['id'],params)
                    for i in range(len(form.ref) - 1):
                        new_title = raw_title.replace("Part ref.", form.ref[i + 1].ref).replace("Part name", form.ref[i + 1].name)
                        copy_task(task['id'],more_info_task['data'][0]['parentIds'][0],new_title,'')
            elif "piezas mecanicas" in valores:
                if len(form.ref) == 0:
                    delete_task(task['id'])


        # Paso 4: Borrar carpetas si su campo es false
        folders = get_folders(main_folder_id)

        for folder in folders['data']:
            customFields = get_folder(folder['id'])['data'][0]['customFields']
            campo = next((f for f in customFields if f['id'] == eco_tag), None)
            if campo is None:
                continue

            valores = json.loads(campo['value'])

            # Booleanos
            if "documentacion" in valores:
                if form.documentacion == False:
                    delete_folder(folder['id'])
            elif "embalaje" in valores and "etiqueta" in valores:
                if form.embalaje == False and form.etiqueta == False:
                    delete_folder(folder['id'])
            elif "embalaje" in valores:
                if form.embalaje == False:
                    delete_folder(folder['id'])
            elif "etiqueta" in valores:
                if form.etiqueta == False:
                    delete_folder(folder['id'])
            elif "pauta montaje" in valores:
                if form.pauta_montaje == False:
                    delete_folder(folder['id'])
            elif "util montaje" in valores:
                if form.util_montaje == False:
                    delete_folder(folder['id'])
            elif "patntes afectados" in valores:
                if form.patentes_afectados == False:
                    delete_folder(folder['id'])
            elif "ensayos" in valores:
                if form.ensayos == False:
                    delete_folder(folder['id'])
            elif "preserie" in valores:
                if form.preserie == False:
                    delete_folder(folder['id'])
            elif "BETAs" in valores:
                if form.BETAs == False:
                    delete_folder(folder['id'])
            elif "utiles test cambio mec" in valores and "utiles test cambio SW" in valores:
                if form.utiles_test_cambio_mec == False and form.utiles_test_cambio_SW == False:
                    delete_folder(folder['id'])
            elif "utiles test cambio mec" in valores:
                if form.utiles_test_cambio_mec == False:
                    delete_folder(folder['id'])
            elif "utiles test cambio SW" in valores:
                if form.utiles_test_cambio_SW == False:
                    delete_folder(folder['id'])
            elif "cert elect" in valores:
                if form.cert_elect == False:
                    delete_folder(folder['id'])
            elif "ESD" in valores:
                if form.ESD == False:
                    delete_folder(folder['id'])
            elif "FW" in valores:
                if form.FW == False:
                    delete_folder(folder['id'])
            elif "cert mec" in valores:
                if form.cert_mec == False:
                    delete_folder(folder['id'])
            elif "electromec" in valores:
                if form.elctromec == False:
                    delete_folder(folder['id'])
            # Circuitos electronicos
            elif "circuitos electronicos" in valores:
                if len(form.circuitos_simp) == 0 and len(form.circuitos_comp) == 0:
                    delete_folder(folder['id'])
            elif "circuito simple" in valores:
                if len(form.circuitos_simp) == 0:
                    delete_folder(folder['id'])
                else:
                    raw_title = folder['title']
                    params['title'] = f'{raw_title.replace("<CircuitName>", form.circuitos_simp[0].name)} (1º loop)'
                    parentId = get_folder(folder['id'])['data'][0]['parentIds']
                    update_folder(folder['id'], params)
                    for j in range(form.circuitos_simp[0].loop - 1):
                        new_title = f'{raw_title.replace("<CircuitName>", form.circuitos_simp[0].name)} ({j + 2}º loop)'
                        copy_folder(folder['id'], parentId[0], new_title, '')

                    for i in range(len(form.circuitos_simp) - 1):
                        for j in range(form.circuitos_simp[i + 1].loop):
                            new_title = f'{raw_title.replace("<CircuitName>", form.circuitos_simp[i + 1].name)} ({j + 1}º loop)'
                            copy_folder(folder['id'], parentId[0], new_title, '')

            elif "circuito complex" in valores:
                if len(form.circuitos_comp) == 0:
                    delete_folder(folder['id'])
                else:
                    raw_title = folder['title']
                    params['title'] = f'{raw_title.replace("<CircuitName>", form.circuitos_comp[0].name)} (1º loop)'
                    parentId = get_folder(folder['id'])['data'][0]['parentIds']
                    update_folder(folder['id'], params)
                    for j in range(form.circuitos_comp[0].loop - 1):
                        new_title = f'{raw_title.replace("<CircuitName>", form.circuitos_comp[0].name)} ({j + 2}º loop)'
                        copy_folder(folder['id'], parentId[0], new_title, '')

                    for i in range(len(form.circuitos_comp) - 1):
                        for j in range(form.circuitos_comp[i + 1].loop):
                            new_title = f'{raw_title.replace("<CircuitName>", form.circuitos_comp[i + 1].name)} ({j + 1}º loop)'
                            copy_folder(folder['id'], parentId[0], new_title, '')

            # Piezas mecanicas
            elif "ref piezas mec afectadas" in valores:
                if len(form.ref) == 0:
                    delete_folder(folder['id'])
                else:
                    more_info_folder = get_folder(folder['id'])
                    raw_title = folder['data'][0]['title']
                    new_title = raw_title.replace("Part ref.", form.ref[0].ref).replace("Part name", form.ref[0].name)
                    params = {
                        'title': new_title
                    }
                    update_folder(folder['id'],params)
                    for i in range(len(form.ref) - 1):
                        new_title = raw_title.replace("Part ref.", form.ref[i + 1].ref).replace("Part name", form.ref[i + 1].name)
                        copy_folder(folder['id'],more_info_folder['data'][0]['parentIds'][0], new_title, '')
            elif "piezas mecanicas" in valores:
                if len(form.ref) == 0:
                    delete_folder(folder['id'])
    Thread(target=procesamiento).start()

    return data['data'][0]['permalink']
