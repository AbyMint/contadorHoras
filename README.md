# Bot de Discord para Seguimiento de Presencias

Este bot de Discord permite a los usuarios seguir los cambios de presencia de otros miembros en un servidor con el proposito de llevar un control de el tiempo de juego de los usuarios.

## Características

- Seguimiento de cambios de estado (en línea, ausente, etc.).
- Notificaciones en un canal específico cuando un usuario seguido cambia su estado o actividad.
- Comando para comenzar a seguir a un miembro.

## Instalación

1. Clona este repositorio:
   ```bash
   git clone <URL_DEL_REPOSITORIO>
   cd <NOMBRE_DEL_REPOSITORIO>
   ```

2. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```

3. Crea un archivo `.env` en la raíz del proyecto y añade tu token de bot:
   ```plaintext
   BOT_TOKEN=TU_TOKEN_AQUI
   ```

## Uso

- Inicia el bot:
   ```bash
   python bot.py
   ```

- Usa el comando `!track @usuario` en Discord para comenzar a seguir a un miembro.
- Usa el comando `!untrack @usuario` para dejar de seguir a un miembro.

## Contribuciones

Las contribuciones son bienvenidas. Siéntete libre de abrir un issue o un pull request.

## Licencia

Este proyecto está bajo la Licencia MIT.
