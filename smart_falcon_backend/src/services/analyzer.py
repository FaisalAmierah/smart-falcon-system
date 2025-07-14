import re
import json
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple
from dateutil.parser import parse
import logging

# إعداد التسجيل
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - %(message)s')

class SmartFalconAnalyzer:
    """
    محرك التحليل الذكي لنظام الصقر الذكي
    يقوم بتحليل الإشارات واتخاذ قرارات التداول بناءً على أداء المحافظ التاريخي
    """
    
    def __init__(self):
        # المجموعات الذهبية المستخرجة من التحليل التاريخي
        self.golden_trio = ["KOL_1", "KOL_15", "KOL_22"]
        self.golden_pairs = [
            ["New Wallet_56", "New Wallet_82"],
            ["KOL_15", "KOL_22"]
        ]
        
        # عتبات القرار
        self.STRONG_BUY_THRESHOLD = 45
        self.BUY_THRESHOLD = 20
        
    def extract_kol_track_data(self, message_text: str) -> Optional[Dict]:
        """
        استخلاص بيانات إشارة KOL Track من نص الرسالة
        """
        try:
            # استخلاص عنوان العقد
            ca_match = re.search(r'solana\s*`?([A-HJ-NP-Za-km-z1-9]{32,44})`?', message_text, re.IGNORECASE)
            if not ca_match:
                ca_match = re.search(r'([A-HJ-NP-Za-km-z1-9]{32,44})', message_text)
                if not ca_match:
                    return None
            
            contract_address = ca_match.group(1)
            
            # استخلاص اسم العملة
            token_name = 'N/A'
            token_match = re.search(r'\d+ wallets bought (.*?) avg', message_text)
            if token_match:
                token_name = token_match.group(1).strip()
            
            # استخلاص تفاصيل المحافظ
            wallets_details = []
            wallet_pattern = r'(\d+)\.\s*(KOL|New Wallet)\s*(\d+).*?MC:\s*\$([\d.,KMB]+)'
            
            for match in re.finditer(wallet_pattern, message_text, re.IGNORECASE):
                wallet_info = {
                    "type": match.group(2).strip(),
                    "id": int(match.group(3)),
                    "mc_at_buy": self._parse_number(match.group(4))
                }
                wallets_details.append(wallet_info)
            
            return {
                "contract_address": contract_address,
                "token_name": token_name,
                "wallets_details": wallets_details,
                "total_wallets_involved": len(wallets_details)
            }
            
        except Exception as e:
            logging.warning(f"خطأ في استخلاص بيانات KOL Track: {e}")
            return None
    
    def extract_phanes_data(self, message_text: str) -> Optional[Dict]:
        """
        استخلاص بيانات Phanes من نص الرسالة
        """
        try:
            # استخلاص عنوان العقد
            ca_match = re.search(r'[├└]\s*`?([A-HJ-NP-Za-km-z1-9]{32,44})`?', message_text, re.MULTILINE)
            if not ca_match:
                ca_match = re.search(r'([A-HJ-NP-Za-km-z1-9]{32,44})', message_text)
                if not ca_match:
                    return None
            
            contract_address = ca_match.group(1)
            
            # استخلاص قيمة ATH
            ath_usd = 0.0
            ath_match = re.search(r'ATH:\s*\$([0-9,]+\.?\d*[KMB]?)', message_text)
            if ath_match:
                ath_usd = self._parse_number(ath_match.group(1))
            
            return {
                "contract_address": contract_address,
                "ath_usd": ath_usd
            }
            
        except Exception as e:
            logging.warning(f"خطأ في استخلاص بيانات Phanes: {e}")
            return None
    
    def calculate_confidence_score(self, participating_wallets: List[str], wallets_performance: List[Dict]) -> Tuple[float, str, List[str]]:
        """
        حساب درجة الثقة للإشارة بناءً على أداء المحافظ المشاركة
        """
        score = 0.0
        reasons = []
        
        # تحويل بيانات الأداء إلى قاموس للوصول السريع
        performance_dict = {}
        for wallet in wallets_performance:
            performance_dict[wallet['wallet_unique_id']] = wallet
        
        # قواعد المجموعات الذهبية (الأولوية القصوى)
        if all(wallet in participating_wallets for wallet in self.golden_trio):
            score += 50
            reasons.append("🏆 المجموعة الذهبية الثلاثية موجودة بالكامل")
        else:
            # فحص الأزواج الذهبية
            for pair in self.golden_pairs:
                if all(wallet in participating_wallets for wallet in pair):
                    score += 35
                    reasons.append(f"💎 الزوج الذهبي {' & '.join(pair)} موجود")
        
        # قواعد المحافظ الفردية
        high_performers = 0
        low_performers = 0
        
        for wallet_id in participating_wallets:
            if wallet_id in performance_dict:
                wallet_data = performance_dict[wallet_id]
                success_rate = wallet_data.get('success_rate', 0)
                total_calls = wallet_data.get('total_calls', 0)
                
                if success_rate >= 0.70:
                    score += 10
                    high_performers += 1
                    reasons.append(f"✅ {wallet_id}: نسبة نجاح عالية ({success_rate:.1%})")
                elif success_rate < 0.15 and total_calls > 5:
                    score -= 15
                    low_performers += 1
                    reasons.append(f"❌ {wallet_id}: أداء ضعيف ({success_rate:.1%})")
                else:
                    score += 2
            else:
                # محفظة جديدة
                score += 2
                reasons.append(f"🆕 {wallet_id}: محفظة جديدة")
        
        # تحديد القرار
        if score >= self.STRONG_BUY_THRESHOLD:
            decision = "STRONG_BUY"
        elif score >= self.BUY_THRESHOLD:
            decision = "BUY"
        else:
            decision = "IGNORE"
        
        # إضافة ملخص النتيجة
        reasons.insert(0, f"📊 النقاط الإجمالية: {score}")
        reasons.insert(1, f"📈 المحافظ عالية الأداء: {high_performers}")
        if low_performers > 0:
            reasons.insert(2, f"📉 المحافظ ضعيفة الأداء: {low_performers}")
        
        return score, decision, reasons
    
    def evaluate_signal_performance(self, initial_ath: float, current_ath: float, signal_time: datetime, evaluation_time_limit_minutes: int = 20) -> Tuple[str, bool]:
        """
        تقييم أداء الإشارة بناءً على تغير ATH
        """
        current_time = datetime.now(timezone.utc)
        time_limit = signal_time + timedelta(minutes=evaluation_time_limit_minutes)
        
        if current_ath > initial_ath:
            return "SUCCESS", True
        elif current_time > time_limit:
            return "FAILURE", True
        else:
            return "PENDING", False
    
    def _parse_number(self, value_str: str) -> float:
        """
        تحويل النص إلى رقم مع دعم الاختصارات (K, M, B)
        """
        if not value_str or not isinstance(value_str, str):
            return 0.0
        
        value_str = str(value_str).lower().replace(',', '').replace('$', '').strip()
        multipliers = {'k': 1_000, 'm': 1_000_000, 'b': 1_000_000_000}
        
        if value_str and value_str[-1] in multipliers:
            try:
                return float(value_str[:-1]) * multipliers[value_str[-1]]
            except (ValueError, TypeError):
                return 0.0
        
        try:
            return float(value_str)
        except (ValueError, TypeError):
            return 0.0
    
    def format_decision_message(self, decision: str, token_name: str, contract_address: str, score: float, reasons: List[str]) -> str:
        """
        تنسيق رسالة القرار النهائي
        """
        if decision == "STRONG_BUY":
            emoji = "🟢"
            decision_text = "توصية شراء قوية"
        elif decision == "BUY":
            emoji = "🟡"
            decision_text = "توصية شراء"
        else:
            emoji = "🔴"
            decision_text = "تجاهل الإشارة"
        
        message = f"""
{emoji} **{decision_text}**

🪙 **العملة:** {token_name}
📋 **العقد:** `{contract_address}`
📊 **النقاط:** {score}

**الأسباب:**
{chr(10).join(f"• {reason}" for reason in reasons)}

⏰ **الوقت:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """.strip()
        
        return message

