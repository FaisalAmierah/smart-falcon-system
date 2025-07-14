#!/usr/bin/env python3
"""
خدمة المستمع الحي لقنوات التيليجرام
تقوم بالاستماع إلى القنوات الثلاث وإرسال الرسائل الجديدة إلى webhook في n8n
"""

import asyncio
import aiohttp
import json
import logging
import os
from datetime import datetime
from telethon import TelegramClient, events
from telethon.tl.types import PeerChannel

# إعداد التسجيل
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s'
)

class SmartFalconListener:
    def __init__(self):
        # إعدادات التيليجرام من متغيرات البيئة
        self.api_id = int(os.getenv('TELEGRAM_API_ID', '0'))
        self.api_hash = os.getenv('TELEGRAM_API_HASH', '')
        self.phone = os.getenv('TELEGRAM_PHONE', '')
        
        # معرفات القنوات
        self.channels = {
            'kol_track': int(os.getenv('KOL_TRACK_CHANNEL_ID', '0')),
            'phanes_nf': int(os.getenv('PHANES_NF_CHANNEL_ID', '0')),
            'phanes_15m': int(os.getenv('PHANES_15M_CHANNEL_ID', '0'))
        }
        
        # رابط webhook
        self.webhook_url = os.getenv('N8N_WEBHOOK_URL', 'http://localhost:5000/webhook/telegram')
        
        # إنشاء عميل التيليجرام
        self.client = TelegramClient('smart_falcon_session', self.api_id, self.api_hash)
        
        # قائمة الرسائل المعالجة لتجنب التكرار
        self.processed_messages = set()
    
    async def start(self):
        """
        بدء خدمة المستمع
        """
        try:
            logging.info("🚀 بدء تشغيل خدمة المستمع الحي...")
            
            # الاتصال بالتيليجرام
            await self.client.start(phone=self.phone)
            logging.info("✅ تم الاتصال بالتيليجرام بنجاح")
            
            # التحقق من القنوات
            await self.verify_channels()
            
            # تسجيل معالجات الأحداث
            self.register_handlers()
            
            logging.info("🎯 المستمع جاهز ويستمع للرسائل الجديدة...")
            
            # تشغيل المستمع
            await self.client.run_until_disconnected()
            
        except Exception as e:
            logging.error(f"❌ خطأ في تشغيل المستمع: {e}")
            raise
    
    async def verify_channels(self):
        """
        التحقق من إمكانية الوصول للقنوات
        """
        for channel_name, channel_id in self.channels.items():
            try:
                entity = await self.client.get_entity(PeerChannel(channel_id))
                logging.info(f"✅ تم التحقق من قناة {channel_name}: {entity.title}")
            except Exception as e:
                logging.warning(f"⚠️ لا يمكن الوصول لقناة {channel_name} ({channel_id}): {e}")
    
    def register_handlers(self):
        """
        تسجيل معالجات الرسائل
        """
        # معالج رسائل KOL Track
        @self.client.on(events.NewMessage(chats=[self.channels['kol_track']]))
        async def handle_kol_track(event):
            await self.process_message(event, 'kol_track')
        
        # معالج رسائل Phanes NF
        @self.client.on(events.NewMessage(chats=[self.channels['phanes_nf']]))
        async def handle_phanes_nf(event):
            await self.process_message(event, 'phanes_nf')
        
        # معالج رسائل Phanes 15M
        @self.client.on(events.NewMessage(chats=[self.channels['phanes_15m']]))
        async def handle_phanes_15m(event):
            await self.process_message(event, 'phanes_15m')
    
    async def process_message(self, event, signal_type):
        """
        معالجة الرسالة الجديدة
        """
        try:
            message_id = f"{event.chat_id}_{event.id}"
            
            # تجنب معالجة الرسالة مرتين
            if message_id in self.processed_messages:
                return
            
            self.processed_messages.add(message_id)
            
            # استخلاص نص الرسالة
            message_text = event.message.message or ""
            
            # تحضير البيانات للإرسال
            payload = {
                'signal_type': signal_type,
                'message_text': message_text,
                'timestamp': datetime.now().isoformat(),
                'channel_id': event.chat_id,
                'message_id': event.id
            }
            
            # إرسال البيانات إلى webhook
            await self.send_to_webhook(payload)
            
            logging.info(f"📨 تم معالجة رسالة {signal_type}: {message_text[:100]}...")
            
        except Exception as e:
            logging.error(f"❌ خطأ في معالجة الرسالة: {e}")
    
    async def send_to_webhook(self, payload):
        """
        إرسال البيانات إلى webhook
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    headers={'Content-Type': 'application/json'},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        logging.info(f"✅ تم إرسال البيانات إلى webhook بنجاح")
                    else:
                        logging.warning(f"⚠️ استجابة غير متوقعة من webhook: {response.status}")
                        
        except asyncio.TimeoutError:
            logging.error("❌ انتهت مهلة الاتصال بـ webhook")
        except Exception as e:
            logging.error(f"❌ خطأ في إرسال البيانات إلى webhook: {e}")

async def main():
    """
    الدالة الرئيسية
    """
    # التحقق من متغيرات البيئة
    required_vars = [
        'TELEGRAM_API_ID', 'TELEGRAM_API_HASH', 'TELEGRAM_PHONE',
        'KOL_TRACK_CHANNEL_ID', 'PHANES_NF_CHANNEL_ID', 'PHANES_15M_CHANNEL_ID'
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        logging.error(f"❌ متغيرات البيئة المفقودة: {missing_vars}")
        return
    
    # إنشاء وتشغيل المستمع
    listener = SmartFalconListener()
    await listener.start()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("🛑 تم إيقاف المستمع بواسطة المستخدم")
    except Exception as e:
        logging.error(f"❌ خطأ عام: {e}")

