# المرحلة الأولى: بناء التطبيق
FROM node:18-alpine AS build
WORKDIR /app

# انسخ كل ملفات المشروع أولاً
COPY . .

# --- التصحيح الأول: إعادة تسمية الملف ليتوافق مع الإعدادات ---
RUN mv src/App.jsx src/main.jsx

# --- التصحيح النهائي: إنشاء ملف إعدادات Vite بطريقة أكثر توافقية ---
RUN echo "import { defineConfig } from 'vite';" > vite.config.js && \
    echo "import react from '@vitejs/plugin-react';" >> vite.config.js && \
    echo "import path from 'path';" >> vite.config.js && \
    echo "" >> vite.config.js && \
    echo "export default defineConfig({" >> vite.config.js && \
    echo "  plugins: [react()]," >> vite.config.js && \
    echo "  resolve: {" >> vite.config.js && \
    echo "    alias: {" >> vite.config.js && \
    echo "      '@': path.resolve(__dirname, './src')," >> vite.config.js && \
    echo "    }," >> vite.config.js && \
    echo "  }," >> vite.config.js && \
    echo "});" >> vite.config.js

# قم بتثبيت pnpm
RUN npm install -g pnpm

# قم بتثبيت الاعتماديات
RUN pnpm install

# قم ببناء التطبيق
RUN pnpm run build

# المرحلة الثانية: تقديم الملفات المبنية باستخدام خادم ويب خفيف
FROM nginx:stable-alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
