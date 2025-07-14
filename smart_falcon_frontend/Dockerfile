# المرحلة الأولى: بناء التطبيق
FROM node:18-alpine AS build
WORKDIR /app
COPY package.json ./
COPY pnpm-lock.yaml ./
RUN npm install -g pnpm
RUN pnpm install
COPY . .
RUN pnpm run build

# المرحلة الثانية: تقديم الملفات المبنية باستخدام خادم ويب خفيف
FROM nginx:stable-alpine
COPY --from=build /app/dist /usr/share/nginx/html
# يخبر الحاوية بالاستماع على المنفذ 80
EXPOSE 80
# الأمر الافتراضي لتشغيل خادم الويب
CMD ["nginx", "-g", "daemon off;"]
