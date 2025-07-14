# المرحلة الأولى: بناء التطبيق
FROM node:18-alpine AS build
WORKDIR /app

# انسخ كل ملفات المشروع أولاً
COPY . .

# --- خطوة تشخيصية: عرض محتويات المجلد ---
# هذا سيظهر لنا هيكل الملفات بالضبط قبل عملية البناء
RUN ls -R

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
