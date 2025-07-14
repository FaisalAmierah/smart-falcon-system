# استخدم صورة بايثون رسمية كنقطة بداية
FROM python:3.10-slim

# عيّن دليل العمل داخل الحاوية
WORKDIR /app

# انسخ ملف المتطلبات أولاً
COPY requirements.txt .

# قم بتثبيت الاعتماديات
RUN pip install --no-cache-dir -r requirements.txt

# انسخ باقي ملفات التطبيق
COPY . .

# الأمر الافتراضي لتشغيل المستمع
CMD ["python", "live_listener.py"]
