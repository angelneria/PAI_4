# Usa una imagen oficial de Python
FROM python:3.12-alpine

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1


# Copia los archivos requeridos
COPY requirements.txt /escapadas_a_tu_medida/
COPY db.sqlite3 /escapadas_a_tu_medida/

# Instala dependencias

RUN apk update && apk add --no-cache \
    gcc \
    musl-dev \
    python3-dev \
    linux-headers \
    build-base
# Establece el directorio de trabajo
WORKDIR /escapadas_a_tu_medida
# Copia el resto de los archivos del proyecto
COPY . /escapadas_a_tu_medida/

# Instala las dependencias del proyecto
RUN pip install --no-cache-dir -r requirements.txt

# Expone el puerto en el que Django ejecutará el servidor
EXPOSE 8000

# Comando de entrada
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]