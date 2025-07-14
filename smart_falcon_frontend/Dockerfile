
# المرحلة الأولى: بناء التطبيق
FROM node:18-alpine AS build

# تحديد مجلد العمل
WORKDIR /app

# انسخ كل ملفات المشروع أولاً
COPY . .

# خطوة تشخيصية: عرض محتويات المجلد (اختيارية)
RUN ls -la

# إعادة تسمية الملف ليتوافق مع الإعدادات
RUN mv src/App.jsx src/main.jsx

# إنشاء ملف إعدادات Vite لتعريف مسار @ بالطريقة الصحيحة
RUN cat > vite.config.js << 'EOF'
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
});
EOF

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

# إنشاء ملف إعدادات nginx مخصص (اختياري)
RUN cat > /etc/nginx/conf.d/default.conf << 'EOF'
server {
    listen 80;
    server_name localhost;
    
    location / {
        root /usr/share/nginx/html;
        index index.html index.htm;
        try_files $uri $uri/ /index.html;
    }
    
    # Handle API requests (إذا كنت تريد توجيه طلبات API)
    location /api/ {
        proxy_pass http://smart_falcon_app:5000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    error_page 500 502 503 504 /50x.html;
    location = /50x.html {
        root /usr/share/nginx/html;
    }
}
EOF

# فتح المنفذ 80
EXPOSE 80

# تشغيل nginx
CMD ["nginx", "-g", "daemon off;"]
