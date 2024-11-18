# Instrucciones

Crear un entorno virtual con el siguiente comando:
```
python -m venv venv
```

Activa el entorno virtual dependiendo del sistema operativo: [Guía](https://docs.python.org/3/library/venv.html#how-venvs-work)


En una terminal, ejecutar los siguientes comandos:

```
cd tailwind
npm install
npm run dev
```

En otra terminal, ejecutar los siguientes comandos:

```
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Para cargar los datos de prueba, ejecutar el siguiente comando:

```
python manage.py loaddata fixtures.json
```