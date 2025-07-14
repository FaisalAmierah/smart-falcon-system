import asyncio
import aiohttp
import logging
from typing import Optional
import os

logging.basicConfig(level=logging.INFO)

class TelegramNotificationService:
    """
    خدمة إرسال الإشعارات عبر التيليجرام
    """
    
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN', '')
        self.channel_id = os.getenv('TELEGRAM_NOTIFICATION_CHANNEL_ID', '')
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
    
    async def send_message(self, message: str, parse_mode: str = 'Markdown') -> bool:
        """
        إرسال رسالة إلى قناة التيليجرام
        """
        if not self.bot_token or not self.channel_id:
            logging.warning("إعدادات التيليجرام غير مكتملة")
            return False
        
        try:
            url = f"{self.base_url}/sendMessage"
            payload = {
                'chat_id': self.channel_id,
                'text': message,
                'parse_mode': parse_mode,
                'disable_web_page_preview': True
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        logging.info("✅ تم إرسال الرسالة بنجاح")
                        return True
                    else:
                        error_text = await response.text()
                        logging.error(f"❌ فشل في إرسال الرسالة: {response.status} - {error_text}")
                        return False
                        
        except Exception as e:
            logging.error(f"❌ خطأ في إرسال الرسالة: {e}")
            return False
    
    def send_message_sync(self, message: str, parse_mode: str = 'Markdown') -> bool:
        """
        إرسال رسالة بشكل متزامن
        """
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.send_message(message, parse_mode))
            loop.close()
            return result
        except Exception as e:
            logging.error(f"❌ خطأ في الإرسال المتزامن: {e}")
            return False
    
    async def send_trading_recommendation(self, decision: str, token_name: str, 
                                        contract_address: str, score: float, 
                                        reasons: list) -> bool:
        """
        إرسال توصية تداول
        """
        if decision == "STRONG_BUY":
            emoji = "🟢"
            decision_text = "توصية شراء قوية"
        elif decision == "BUY":
            emoji = "🟡"
            decision_text = "توصية شراء"
        else:
            return False  # لا نرسل إشعارات للإشارات المرفوضة
        
        message = f"""
{emoji} **{decision_text}**

🪙 **العملة:** {token_name}
📋 **العقد:** `{contract_address}`
📊 **النقاط:** {score}

**الأسباب:**
{chr(10).join(f"• {reason}" for reason in reasons)}

⏰ **الوقت:** {asyncio.get_event_loop().time()}

#SmartFalcon #CryptoSignal
        """.strip()
        
        return await self.send_message(message)
    
    async def send_performance_update(self, signal_id: str, token_name: str,
                                    performance_status: str, profit_multiplier: float) -> bool:
        """
        إرسال تحديث أداء الإشارة
        """
        if performance_status == "SUCCESS":
            emoji = "✅"
            status_text = "نجحت الإشارة"
            profit_text = f"📈 **الربح:** {profit_multiplier:.2f}x"
        elif performance_status == "FAILURE":
            emoji = "❌"
            status_text = "فشلت الإشارة"
            profit_text = "📉 **النتيجة:** لم تحقق ربحاً"
        else:
            return False
        
        message = f"""
{emoji} **{status_text}**

🪙 **العملة:** {token_name}
🆔 **معرف الإشارة:** {signal_id}
{profit_text}

#SmartFalcon #PerformanceUpdate
        """.strip()
        
        return await self.send_message(message)
    
    async def send_system_alert(self, alert_type: str, message: str) -> bool:
        """
        إرسال تنبيه نظام
        """
        emoji_map = {
            'error': '🚨',
            'warning': '⚠️',
            'info': 'ℹ️',
            'success': '✅'
        }
        
        emoji = emoji_map.get(alert_type, 'ℹ️')
        
        alert_message = f"""
{emoji} **تنبيه النظام**

{message}

⏰ **الوقت:** {asyncio.get_event_loop().time()}

#SmartFalcon #SystemAlert
        """.strip()
        
        return await self.send_message(alert_message)

# إنشاء مثيل عام للخدمة
telegram_service = TelegramNotificationService()

