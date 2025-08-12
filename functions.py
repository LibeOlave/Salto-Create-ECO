import requests
from constants import BASE_URL, HEADERS, SSL
from html import unescape
import json
import time


# Función para copiar una carpeta
def copy_folder(folder_id, parent_id, title, prefix):
    params = {
        'parent': parent_id,
        'title': title,
        'titlePrefix': prefix
    }
    response = requests.post(
        f'{BASE_URL}/copy_folder/{folder_id}',
        headers=HEADERS,
        params=params,
        verify=SSL
    )
    if response.status_code != 200:
        print(f'Error al copiar carpeta {title}: {response.status_code} - {response.text}')
    return response.json()

def copy_task(task_id, parent_id, title, prefix):
    response = requests.get(
        f'{BASE_URL}/tasks/{task_id}',
        headers=HEADERS,
        verify=SSL
    )
    if response.status_code != 200:
        print(f'Error al obtener la información para copiar la tarea {title}: {response.status_code} - {response.text}')

    params_tarea_original = response.json()['data'][0]
    params = {
        'title': title,
        'description': params_tarea_original.get('description'),
        'status': params_tarea_original.get('status'),
        'importance': params_tarea_original.get('importance'),
        #'dates': params_tarea_original.get('dates'),
        'shareds': params_tarea_original.get('shareds'),
        'parents': params_tarea_original.get('parents'),
        'responsibles': params_tarea_original.get('responsibles'),
        'responsiblePlaceholders': params_tarea_original.get('responsiblePlaceholders'),
        'followers': params_tarea_original.get('followers'),
        'follow': params_tarea_original.get('follow'),
        'priorityBefore': params_tarea_original.get('priorityBefore'),
        'priorityAfter': params_tarea_original.get('priorityAfter'),
        'superTasks': params_tarea_original.get('superTasks'),
        'metadata': params_tarea_original.get('metadata'),
        'customFields': params_tarea_original.get('customFields'),
        'customStatus': params_tarea_original.get('customStatus'),
        'effortAllocation': params_tarea_original.get('effortAllocation'),
        'billingType': params_tarea_original.get('billingType'),
        'withInvitations': params_tarea_original.get('withInvitations'),
        'customItemTypeId': params_tarea_original.get('customItemTypeId'),
        'plainTextCustomFields': params_tarea_original.get('plainTextCustomFields'),
        'fields': params_tarea_original.get('fields')
    }

    response = requests.post(
        f'{BASE_URL}/folders/{parent_id}/tasks',
        headers=HEADERS,
        json=params,
        verify=SSL
    )
    if response.status_code != 200:
        print(f'Error al copiar tarea {title}: {response.status_code} - {response.text}')
    update_task_dates(
        response.json()['data'][0]['id'],
        params_tarea_original.get('dates', {}).get('start'),
        params_tarea_original.get('dates', {}).get('due')
    )
                      
    return response.json()

# Función para copiar una carpeta del blueprint
def copy_blueprint_folder(folder_id, parent_id, title, prefix, fecha_inicio):
    try:
        params = {
            'parent': parent_id,
            'title': title,
            'titlePrefix': prefix,
            'rescheduleDate': fecha_inicio
        }

        # Lanzar el trabajo
        response = requests.post(
            f'{BASE_URL}/folder_blueprints/{folder_id}/launch_async',
            headers=HEADERS,
            params=params,
            verify=SSL
        )

        if response.status_code not in [200, 202]:
            print(f'Error al lanzar el trabajo async para {title}: {response.status_code} - {response.text}')
            return None

        job_data = response.json().get('data', [])
        if not job_data or not job_data[0].get('id'):
            print(f"No se obtuvo ID del trabajo async: {response.text}")
            return None

        job_id = job_data[0]['id']

        # Esperar a que se complete el trabajo
        max_retries = 30
        retry = 0
        while retry < max_retries:
            estado = requests.get(
                f'{BASE_URL}/async_job/{job_id}',
                headers=HEADERS,
                verify=SSL
            )
            estado_json = estado.json()
            if estado_json['data'][0]['status'] == 'Completed':
                break
            elif estado_json.get('status') == 'Failed':
                print(f"El trabajo async falló: {estado_json}")
                return None
            time.sleep(2)
            retry += 1
        else:
            print("Timeout esperando a que el trabajo async se complete.")
            return None

        created_folder_id = estado_json['data'][0]['result']['folderId']
        if not created_folder_id:
            print("No se obtuvo el ID de la carpeta creada.")
            return None

        # Obtener datos de la carpeta creada
        response = requests.get(
            f'{BASE_URL}/folders/{created_folder_id}',
            headers=HEADERS,
            verify=SSL
        )
        if response.status_code != 200:
            print(f"Error al obtener carpeta creada: {response.status_code} - {response.text}")
            return None

        return response.json()

    except Exception as e:
        print(f"Error inesperado en copy_blueprint_folder: {e}")
        return None

# Función para obtener id de una carpeta a partir del titulo
def get_folderId(parent_id, title, prefix):
    id = ''
    response = requests.get(
        f'{BASE_URL}/folders/{parent_id}/folders',
        headers=HEADERS,
        verify=SSL
    )
    if response.status_code != 200:
        print(f'Error al obtener ids de las tareas {title}: {response.status_code} - {response.text}')
    for folder in response.json().get('data', []):
        folder_title = unescape(folder.get('title', ''))
        if folder_title == f'{prefix}{title}':
            id = unescape(folder.get('id', ''))
    return id

# Función para obtener id de una tarea a partir del titulo
def get_taskId(parent_id, title, prefix):
    id = ''
    params = {
        'title': f'{prefix}{title}'
    }
    response = requests.get(
        f'{BASE_URL}/folders/{parent_id}/tasks',
        headers=HEADERS,
        verify=SSL
    )
    if response.status_code != 200:
        print(f'Error al obtener ids de las tareas {title}: {response.status_code} - {response.text}')
    for task in response.json().get('data', []):
        task_title = unescape(task.get('title', ''))
        if task_title == f'{prefix}{title}':
            id = unescape(task.get('id', ''))
    return id

# Función para borrar una tarea
def delete_task(id):
    response = requests.delete(
        f'{BASE_URL}/tasks/{id}',
        headers=HEADERS,
        verify=SSL
    )
    if response.status_code != 200:
        print(f'Error al borrar la tarea con el id {id}: {response.status_code} - {response.text}')

def delete_folder(id):
    response = requests.delete(
        f'{BASE_URL}/folders/{id}',
        headers=HEADERS,
        verify=SSL
    )
    if response.status_code != 200:
        print(f'Error al borrar la carpeta con el id {id}: {response.status_code} - {response.text}')


def get_folders(parent_id):
    response = requests.get(
        f'{BASE_URL}/folders/{parent_id}/folders',
        headers=HEADERS,
        verify=SSL
    )
    if response.status_code != 200:
        print(f'Error al obtener las carpetas de la carpeta {response.json().get("data")[0]["title"]}: {response.status_code} - {response.text}')
    return response.json()

def get_folder(folder_id):
    response = requests.get(
        f'{BASE_URL}/folders/{folder_id}',
        headers=HEADERS,
        verify=SSL
    )
    if response.status_code != 200:
        print(f'Error al obtener las carpetas de la carpeta {response.json().get("data")[0]["title"]}: {response.status_code} - {response.text}')
    return response.json()

def update_folder(folder_id,params):
    response = requests.put(
        f'{BASE_URL}/folders/{folder_id}',
        headers=HEADERS,
        verify=SSL,
        json=params
    )
    if response.status_code != 200:
        print(f'Error al obtener las actualizar de la carpeta {response.json().get("data")[0]["title"]}: {response.status_code} - {response.text}')
    return response.json()

def update_task(task_id,params):
    response = requests.put(
        f'{BASE_URL}/tasks/{task_id}',
        headers=HEADERS,
        verify=SSL,
        json=params
    )
    if response.status_code != 200:
        print(f'Error al actualizar de la tarea {response.json().get("data")[0]["title"]}: {response.status_code} - {response.text}')
    return response.json()

def get_tasks(parent_id):
    response = requests.get(
        f'{BASE_URL}/folders/{parent_id}/tasks?descendants=True',
        headers=HEADERS,
        verify=SSL
    )
    if response.status_code != 200:
        print(f'Error al obtener las carpetas de la carpeta {response.json().get("data")[0]["title"]}: {response.status_code} - {response.text}')
    return response.json()

def get_task(task_id):
    response = requests.get(
        f'{BASE_URL}/tasks/{task_id}',
        headers=HEADERS,
        verify=SSL
    )
    if response.status_code != 200:
        print(f'Error al obtener las carpetas de la carpeta {response.json().get("data")[0]["title"]}: {response.status_code} - {response.text}')
    return response.json()

def update_task_dates(task_id, start, due):
    dates_payload = {
        'dates': {
            'type': 'Planned',
            'start': start,
            'due': due
        }
    }

    response = requests.put(
        f'{BASE_URL}/tasks/{task_id}',
        headers=HEADERS,
        json=dates_payload,
        verify=SSL
    )

    if response.status_code != 200:
        print(f'Error al actualizar fechas de la tarea {task_id}: {response.status_code} - {response.text}')
    return response.json()
