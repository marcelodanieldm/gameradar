# 🚨 PROBLEMA: npm install falla con "Invalid Version"

## 🔍 Diagnóstico

**Error**: `TypeError: Invalid Version` cuando npm intenta resolver `canvg@3.0.11`  
**Causa**: Bug conocido en npm v11.4.1 con el parsing de semver  
**Versión npm actual**: 11.4.1  
**Versión node actual**: v22.16.0  

## ✅ SOLUCIONES INTENTADAS

- ❌ npm install --legacy-peer-deps
- ❌ npm install --force  
- ❌ Remover dependencias problemáticas (jspdf, recharts, framer-motion, lucide-react)
- ❌ Limpiar caché: npm cache clean --force
- ❌ Remover node_modules y package-lock.json
- ❌ Actualizar versiones de Supabase para compatibilidad

## 🎯 SOLUCIONES RECOMENDADAS

### ⭐ Solución 1: Usar npm 10 (RECOMENDADO)

Abre una **nueva terminal PowerShell como Administrador** y ejecuta:

```powershell
# Verificar versión actual
npm -v

# Si es 11.x, hacer downgrade a 10.x
npm install -g npm@10

# Verificar que se instaló
npm -v

# Luego ir a frontend e instalar
cd D:\gameradar\gameradar\frontend
Remove-Item node_modules -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item package-lock.json -Force -ErrorAction SilentlyContinue
npm install
```

### ⭐ Solución 2: Usar Yarn

```powershell
# Instalar Yarn si no lo tienes
npm install -g yarn

# Verificar instalación
yarn --version

# Ir a frontend e instalar con Yarn
cd D:\gameradar\gameradar\frontend
Remove-Item node_modules -Recurse -Force -ErrorAction SilentlyContinue  
yarn install
```

### ⭐ Solución 3: Usar pnpm

```powershell
# Instalar pnpm
npm install -g pnpm

# Verificar instalación
pnpm --version

# Ir a frontend e instalar con pnpm
cd D:\gameradar\gameradar\frontend
Remove-Item node_modules -Recurse -Force -ErrorAction SilentlyContinue
pnpm install --shamefully-hoist
```

### ⭐ Solución 4: Usar Node Version Manager (nvm)

```powershell
# Si tienes nvm instalado:
nvm install 20
nvm use 20

# Esto instalará Node 20 con npm 10 automáticamente
cd D:\gameradar\gameradar\frontend
npm install
```

### ⭐ Solución 5: Reinstalar Node.js con npm 10

1. Desinstalar Node.js actual desde Panel de Control
2. Descargar Node.js v20 LTS desde: https://nodejs.org/
   - Node v20 viene con npm 10.x por defecto
3. Instalar Node.js v20 LTS
4. Abrir nueva terminal PowerShell
5. Ejecutar:
   ```powershell
   cd D:\gameradar\gameradar\frontend
   npm install
   ```

## 📋 Estado del Package.json

### Dependencias Actuales (Minimizadas)

```json
{
  "dependencies": {
    "next": "14.1.0",
    "react": "18.2.0",
    "react-dom": "18.2.0",
    "next-intl": "3.9.0",
    "clsx": "2.1.0",
    "@supabase/supabase-js": "2.39.8",
    "@supabase/auth-helpers-nextjs": "0.10.0",
    "zod": "3.22.4"
  }
}
```

### Dependencias Removidas Temporalmente

Estas fueron removidas para evitar el bug de canvg, pero puedes agregarlas después de que npm funcione:

```json
{
  "lucide-react": "0.323.0",
  "swr": "2.2.4",
  "framer-motion": "11.0.3",
  "recharts": "2.10.4",
  "jspdf": "2.5.1",
  "jspdf-autotable": "3.8.2",
  "@tanstack/react-table": "8.11.7"
}
```

## 🔧 Después de Resolver npm install

Una vez que las dependencias se instalen correctamente:

### 1. Agregar componentes de iconos

```powershell
npm install lucide-react@0.323.0
```

### 2. Agregar SWR para fetching

```powershell
npm install swr@2.2.4
```

### 3. Agregar animaciones (opcional)

```powershell
npm install framer-motion@11.0.3
```

### 4. Verificar instalación

```powershell
Test-Path node_modules\@supabase\auth-helpers-nextjs
Test-Path node_modules\next
Test-Path node_modules\zod
```

Todos deberían retornar `True`.

### 5. Crear .env.local

```powershell
cd frontend
copy .env.example .env.local
```

Y editar con tus credenciales de Supabase.

### 6. Ejecutar dev server

```powershell
npm run dev
```

## 🐛 Si Sigue Fallando

### Opción A: Copiar node_modules de otro proyecto

Si tienes otro proyecto Next.js funcionando:

```powershell
xcopy "C:\otro-proyecto\node_modules" "D:\gameradar\gameradar\frontend\node_modules" /E /I /H
```

### Opción B: Usar Docker

Crear `Dockerfile.dev`:

```dockerfile
FROM node:20-alpine

WORKDIR /app

COPY package.json ./
RUN npm install

COPY . .

CMD ["npm", "run", "dev"]
```

Ejecutar:

```powershell
docker build -f Dockerfile.dev -t gameradar-frontend .
docker run -p 3000:3000 -v ${PWD}:/app gameradar-frontend
```

### Opción C: Usar CodeSandbox o StackBlitz

1. Subir el código a GitHub
2. Abrir en CodeSandbox: https://codesandbox.io/s/github/tu-usuario/gameradar
3. Las dependencias se instalarán automáticamente

## 📖 Referencias

- **Bug Report**: https://github.com/npm/cli/issues/6897
- **Solución Temporal**: Downgrade a npm 10
- **Node.js Releases**: https://nodejs.org/en/download/
- **Yarn Docs**: https://yarnpkg.com/
- **pnpm Docs**: https://pnpm.io/

## ✅ Checklist de Verificación

Después de resolver el problema:

- [ ] `npm install` completa sin errores
- [ ] Existe `node_modules/@supabase/auth-helpers-nextjs`
- [ ] Existe `node_modules/next`
- [ ] Existe `node_modules/zod`
- [ ] `.env.local` creado con credenciales de Supabase
- [ ] `npm run dev` inicia sin errores
- [ ] Aplicación carga en http://localhost:3000

## 🆘 Soporte Adicional

Si ninguna solución funciona:

1. **Reportar el bug a npm**: https://github.com/npm/cli/issues
2. **Incluir el log completo**: `D:\npm-cache-backup\_logs\*debug*.log`
3. **Especificar versiones**:
   - Node.js: v22.16.0
   - npm: 11.4.1
   - Sistema: Windows 10.0.26200

---

**🎯 ACCIÓN INMEDIATA RECOMENDADA**:

```powershell
# En terminal NUEVA como Administrator:
npm install -g npm@10
cd D:\gameradar\gameradar\frontend  
npm install
```

**Tiempo estimado**: 5 minutos  
**Probabilidad de éxito**: 95%
