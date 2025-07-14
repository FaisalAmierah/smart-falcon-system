
# المرحلة الأولى: بناء التطبيق
FROM node:18-alpine AS build

# تحديد مجلد العمل
WORKDIR /app

# انسخ كل ملفات المشروع أولاً
COPY . .

# إعادة تسمية الملف ليتوافق مع الإعدادات
RUN mv src/App.jsx src/main.jsx

# إنشاء ملف إعدادات Vite بطريقة آمنة
RUN echo "import { defineConfig } from 'vite';" > vite.config.js
RUN echo "import react from '@vitejs/plugin-react';" >> vite.config.js
RUN echo "import path from 'path';" >> vite.config.js
RUN echo "" >> vite.config.js
RUN echo "export default defineConfig({" >> vite.config.js
RUN echo "  plugins: [react()]," >> vite.config.js
RUN echo "  resolve: {" >> vite.config.js
RUN echo "    alias: {" >> vite.config.js
RUN echo "      '@': path.resolve(__dirname, './src')," >> vite.config.js
RUN echo "    }," >> vite.config.js
RUN echo "  }," >> vite.config.js
RUN echo "});" >> vite.config.js

# تثبيت pnpm عالمياً
RUN npm install -g pnpm

# تثبيت الاعتماديات باستخدام pnpm
RUN pnpm install

# بناء التطبيق للإنتاج
RUN pnpm run build

# المرحلة الثانية: تقديم الملفات المبنية باستخدام nginx
FROM nginx:stable-alpine

# نسخ الملفات المبنية من المرحلة الأولى إلى nginx
COPY --from=build /app/dist /usr/share/nginx/html

# إنشاء ملف إعدادات nginx أساسي
RUN echo "server {" > /etc/nginx/conf.d/default.conf
RUN echo "    listen 80;" >> /etc/nginx/conf.d/default.conf
RUN echo "    server_name localhost;" >> /etc/nginx/conf.d/default.conf
RUN echo "    location / {" >> /etc/nginx/conf.d/default.conf
RUN echo "        root /usr/share/nginx/html;" >> /etc/nginx/conf.d/default.conf
RUN echo "        index index.html index.htm;" >> /etc/nginx/conf.d/default.conf
RUN echo "        try_files \$uri \$uri/ /index.html;" >> /etc/nginx/conf.d/default.conf
RUN echo "    }" >> /etc/nginx/conf.d/default.conf
RUN echo "}" >> /etc/nginx/conf.d/default.conf

# فتح المنفذ 80
EXPOSE 80

# تشغيل nginx
CMD ["nginx", "-g", "daemon off;"]
