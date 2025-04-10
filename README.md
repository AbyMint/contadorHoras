# Bot de Discord para Seguimiento de Presencias

Este bot de Discord permite a los usuarios seguir los cambios de presencia de otros miembros en un servidor con el proposito de llevar un control de el tiempo de juego de los usuarios.

## Características

- Seguimiento de cambios de estado (en línea, ausente, etc.).
- Notificaciones en un canal específico cuando un usuario seguido cambia su estado o actividad.
- Registro del tiempo de juego para cada juego que los usuarios rastreados juegan.
- Visualización del tiempo total jugado por juego para cada usuario.

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

## Comandos disponibles
- !track [@usuario]: Comienza a seguir a un usuario y registrar su tiempo de juego. Si no se especifica un usuario, se seguirá al autor del comando.
- !untrack [@usuario]: Deja de seguir a un usuario y elimina su registro de tiempo de juego. Si no se especifica un usuario, se dejará de seguir al autor del comando.
- !playtime [@usuario]: Muestra el tiempo total jugado en cada juego para el usuario especificado. Si no se especifica un usuario, se mostrará la información del autor del comando.
## Funcionamiento
El bot registra automáticamente cuando un usuario comienza y termina de jugar a un juego, calculando el tiempo total jugado. Las actualizaciones de presencia se notifican en el canal "botargas" del servidor.


## Contribuciones

Las contribuciones son bienvenidas. Siéntete libre de abrir un issue o un pull request.

## Licencia

Este proyecto está bajo la Licencia MIT.
