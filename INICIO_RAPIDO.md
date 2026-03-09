# 🚀 INICIO RÁPIDO - 10 Minutos

## ⚡ Comando por Comando

### Paso 1: Instalar Node.js v20 (5 min)
1. Descargar: https://nodejs.org/ (botón verde)
2. Instalar
3. Cerrar TODAS las terminales

### Paso 2: Instalar Dependencias (2 min)
```powershell
cd D:\gameradar\gameradar\frontend
npm install
```

### Paso 3: Configurar Supabase (2 min)
1. Ir a: https://app.supabase.com
2. Crear proyecto "GameRadar"
3. Settings → API → Copiar:
   - Project URL
   - anon public key  
   - service_role key
4. Editar `frontend/.env.local`:
```bash
NEXT_PUBLIC_SUPABASE_URL=TU-URL-AQUI
NEXT_PUBLIC_SUPABASE_ANON_KEY=TU-ANON-KEY-AQUI
SUPABASE_SERVICE_ROLE_KEY=TU-SERVICE-KEY-AQUI
```

### Paso 4: Ejecutar SQL (1 min)
1. En Supabase → SQL Editor → New query
2. Copiar TODO `supabase/migrations/002_subscription_security.sql`
3. Pegar y Run

### Paso 5: Iniciar (30 seg)
```powershell
npm run dev
```
Abrir: http://localhost:3000

---

## ✅ Verificación Rápida

```powershell
# Todo debe retornar True:
Test-Path node_modules\next
Test-Path node_modules\@supabase\auth-helpers-nextjs
Test-Path .env.local
```

---

## 🆘 Si hay problemas

- **npm install falla**: Ver [NPM_INSTALL_PROBLEM.md](NPM_INSTALL_PROBLEM.md)
- **Otros errores**: Ver [PASOS_FINALES.md](PASOS_FINALES.md)

---

## ✨ ¡Listo!

Tu app está segura y funcionando. Todo el código ya está implementado. 🎉
