# المرحلة الأولى: بناء التطبيق
FROM node:18-alpine AS build
WORKDIR /app

# انسخ كل ملفات المشروع أولاً
# هذا يضمن أن كل الملفات، بما في ذلك index.html و src/، موجودة قبل أي خطوة أخرى
COPY . .

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
