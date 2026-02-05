# 🚀 Guía de Setup para GitHub Actions

## 📋 Checklist de Configuración

- [ ] Repositorio en GitHub creado
- [ ] Código subido al repositorio
- [ ] Secrets configurados
- [ ] Schema SQL aplicado en Supabase
- [ ] Workflow activado
- [ ] Primer ejecución exitosa

## 1️⃣ Crear Repositorio en GitHub

```bash
# Inicializar git en tu proyecto
cd d:\gameradar\gameradar
git init

# Añadir remote
git remote add origin https://github.com/tu-usuario/gameradar-ai.git

# Primer commit
git add .
git commit -m "🎮 Initial commit - GameRadar AI"
git branch -M main
git push -u origin main
```

## 2️⃣ Configurar Secrets en GitHub

### Ir a: Repository → Settings → Secrets and variables → Actions

### Secrets Requeridos:

1. **SUPABASE_URL**
   ```
   https://xxxxxxxxxxx.supabase.co
   ```

2. **SUPABASE_KEY**
   ```
   eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.ey...
   ```
   ⚠️ Usar el "anon/public" key, no el service_role key

3. **AIRTABLE_API_KEY** (opcional)
   ```
   patXXXXXXXXXXXXXXXX.xxxxxxxxxxxxxxxxxxxxxxx
   ```

4. **AIRTABLE_BASE_ID** (opcional)
   ```
   appXXXXXXXXXXXXXX
   ```

5. **AIRTABLE_TABLE_NAME** (opcional)
   ```
   GameRadar_Players
   ```

### Secrets Opcionales para Proxies:

6. **BRIGHT_DATA_USERNAME** (si usas Bright Data)
   ```
   your-username-here
   ```

7. **BRIGHT_DATA_PASSWORD**
   ```
   your-password-here
   ```

8. **SCRAPERAPI_KEY** (si usas ScraperAPI)
   ```
   your-api-key
   ```

9. **PROXY_LIST** (si usas proxies custom)
   ```
   host1:port1:user1:pass1,host2:port2:user2:pass2
   ```

## 3️⃣ Obtener Credenciales de Supabase

### Paso a paso:

1. Ve a [supabase.com](https://supabase.com)
2. Login o crea una cuenta
3. Crea un nuevo proyecto o selecciona uno existente
4. Ve a Settings → API
5. Copia:
   - **URL**: Project URL
   - **Key**: Project API keys → `anon` `public`

### Aplicar el Schema SQL:

1. En Supabase Dashboard
2. Ve a SQL Editor
3. Click "New query"
4. Pega el contenido de `database_schema.sql`
5. Click "Run" o `Ctrl+Enter`

Deberías ver:
```
✓ Tables created: 3
✓ Functions created: 4
✓ Triggers created: 3
✓ Views created: 2
```

## 4️⃣ Obtener Credenciales de Airtable (Opcional)

### Paso a paso:

1. Ve a [airtable.com](https://airtable.com)
2. Login o crea una cuenta
3. Crea una Base nueva llamada "GameRadar AI"
4. Crea una tabla llamada "GameRadar_Players" con campos:
   - nickname (Single line text)
   - game (Single line text)
   - country (Single line text)
   - rank (Single line text)
   - win_rate (Number)
   - kda (Number)
   - top_champion_1 (Single line text)
   - top_champion_2 (Single line text)
   - top_champion_3 (Single line text)
   - profile_url (URL)
   - scraped_at (Date)

5. Para obtener API Key:
   - Click en tu perfil (esquina superior derecha)
   - Account → Developer hub
   - Crea un Personal Access Token
   - Scopes: `data.records:read`, `data.records:write`

6. Para obtener Base ID:
   - Abre tu Base en Airtable
   - Ve a Help → API documentation
   - El Base ID está en la URL: `https://airtable.com/appXXXXXXXXXXXXXX/api/docs`

## 5️⃣ Activar el Workflow

### Verificar que el workflow está activo:

1. Ve a tu repositorio en GitHub
2. Click en la pestaña "Actions"
3. Deberías ver "🥷 Ninja E-sports Scraper" en la lista

### Ejecutar manualmente:

1. Click en el workflow "🥷 Ninja E-sports Scraper"
2. Click "Run workflow" (dropdown)
3. Selecciona "main" branch
4. Click "Run workflow" (botón verde)

### Ver resultados:

1. Espera unos segundos
2. Verás una nueva ejecución en la lista
3. Click en ella para ver detalles
4. Expande cada paso para ver logs

## 6️⃣ Configurar Proxies (Opcional)

### Opción A: Bright Data (Luminati)

1. Registro en [brightdata.com](https://brightdata.com)
2. Crea una zona de proxy
3. Obtén credenciales:
   - Username: `brd-customer-XXX-zone-YYY`
   - Password: tu password
   - Host: `brd.superproxy.io`
   - Port: `22225`

### Opción B: ScraperAPI

1. Registro en [scraperapi.com](https://scraperapi.com)
2. Copia tu API Key del dashboard
3. No necesitas más configuración

### Opción C: Proxies Custom

1. Consigue una lista de proxies (free o paid)
2. Formato: `host:port:user:pass`
3. Separa múltiples proxies con comas

## 7️⃣ Testing Local

Antes de pushear a GitHub, prueba localmente:

```bash
# 1. Instalar dependencias
pip install -r requirements.txt
playwright install chromium

# 2. Crear .env con tus credenciales
cp .env.example .env
# Editar .env con tus valores

# 3. Ejecutar tests
python test_ninja_scraper.py

# 4. Ejecutar scraper
python cnn_brasil_scraper.py
```

## 8️⃣ Monitoreo y Mantenimiento

### Ver ejecuciones programadas:

- GitHub Actions se ejecuta automáticamente cada 6 horas
- Revisa el tab "Actions" para ver historial

### Configurar notificaciones:

```yaml
# En .github/workflows/ninja_scraper.yml
- name: 🔔 Notify on failure
  if: failure()
  uses: rtCamp/action-slack-notify@v2
  env:
    SLACK_WEBHOOK: ${{ secrets.SLACK_WEBHOOK }}
    SLACK_MESSAGE: 'Ninja scraper failed!'
```

### Ajustar frecuencia:

```yaml
# Cada 2 horas
schedule:
  - cron: '0 */2 * * *'

# Cada día a medianoche
schedule:
  - cron: '0 0 * * *'

# Cada lunes a las 9am
schedule:
  - cron: '0 9 * * 1'
```

## 🚨 Troubleshooting

### Error: "Secrets not found"
- Verifica que los secrets están configurados en Settings → Secrets
- Los nombres deben coincidir exactamente (case-sensitive)

### Error: "Playwright not installed"
- El workflow instala automáticamente Playwright
- Si falla, verifica el paso "Install Playwright browsers"

### Error: "Supabase connection failed"
- Verifica que SUPABASE_URL tiene el formato correcto
- Verifica que SUPABASE_KEY es el anon/public key
- Confirma que el schema SQL está aplicado

### Error: "No players scraped"
- La estructura de CNN Brasil puede haber cambiado
- Ejecuta localmente con `headless=False` para debug
- Ajusta los selectores CSS en `cnn_brasil_scraper.py`

### Workflow no se ejecuta automáticamente
- Verifica que el cron está bien formateado
- GitHub Actions requiere al menos 1 commit en main
- El primer cron puede tardar hasta 1 hora

## 📊 Métricas de Éxito

Una ejecución exitosa debe mostrar:
```
✅ Ninja scraper completed successfully!
📊 Results:
  - Scraped: 50-100 players
  - Errors: 0-5 (aceptable)
  - Duration: 30-60s
```

## 🔐 Seguridad Best Practices

✅ **NUNCA** commits tu archivo `.env`
✅ **SIEMPRE** usa Secrets de GitHub para credenciales
✅ **Usa** el anon/public key de Supabase, no service_role
✅ **Rota** tus API keys regularmente
✅ **Revisa** logs para detectar accesos no autorizados

## 📚 Recursos Adicionales

- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [Supabase Docs](https://supabase.com/docs)
- [Playwright Docs](https://playwright.dev/)
- [Airtable API](https://airtable.com/developers/web/api/introduction)

---

**¿Listo para lanzar?** 🚀

```bash
git push origin main
```

Luego ve a Actions tab y observa la magia! 🥷✨
