
# استخدم صورة بايثون رسمية كنقطة بداية
FROM python:3.10-slim

# عيّن دليل العمل داخل الحاوية ليكون /app
WORKDIR /app

# تثبيت الاعتماديات النظامية المطلوبة
RUN apt-get update && apt-get install -y \
    gcc \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# انسخ ملف المتطلبات أولاً للاستفادة من التخزين المؤقت لـ Docker
COPY requirements.txt .

# قم بتثبيت الاعتماديات (Dependencies) المذكورة في الملف
RUN pip install --no-cache-dir -r requirements.txt

# انسخ باقي ملفات التطبيق (بما في ذلك مجلد src) إلى دليل العمل داخل الحاوية
COPY . .

# عرّض المنفذ الذي يعمل عليه تطبيق Flask (المنفذ الافتراضي لـ Flask هو 5000)
EXPOSE 5000

# الأمر الافتراضي لتشغيل التطبيق من المسار الصحيح داخل الحاوية
CMD ["python", "src/main.py"]
