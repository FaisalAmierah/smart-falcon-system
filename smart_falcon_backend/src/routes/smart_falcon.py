from flask import Blueprint, request, jsonify
from src.models.user import db
from src.models.smart_falcon import Wallet, Signal, SignalWalletLink, TelegramMessage, SystemConfig
from src.services.analyzer import SmartFalconAnalyzer
from src.services.telegram_service import telegram_service
from datetime import datetime, timezone
import json
import uuid
import logging
import asyncio

# إعداد التسجيل
logging.basicConfig(level=logging.INFO)

smart_falcon_bp = Blueprint('smart_falcon', __name__)
analyzer = SmartFalconAnalyzer()

@smart_falcon_bp.route('/webhook/telegram', methods=['POST'])
def telegram_webhook():
    """
    نقطة استقبال الرسائل من خدمة المستمع الحي
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'لا توجد بيانات'}), 400
        
        signal_type = data.get('signal_type')
        message_text = data.get('message_text')
        
        if not signal_type or not message_text:
            return jsonify({'error': 'بيانات ناقصة'}), 400
        
        # حفظ الرسالة في قاعدة البيانات
        message_id = str(uuid.uuid4())
        telegram_message = TelegramMessage(
            message_id=message_id,
            channel_type=signal_type,
            message_text=message_text,
            received_time=datetime.now(timezone.utc)
        )
        db.session.add(telegram_message)
        
        # معالجة الرسالة حسب النوع
        if signal_type == 'kol_track':
            result = process_kol_track_signal(message_text, message_id)
        elif signal_type in ['phanes_nf', 'phanes_15m']:
            result = process_phanes_update(message_text, signal_type)
        else:
            result = {'error': 'نوع إشارة غير معروف'}
        
        # تحديث نتيجة المعالجة
        telegram_message.processed = True
        telegram_message.processing_result = json.dumps(result)
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message_id': message_id,
            'processing_result': result
        })
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"خطأ في معالجة webhook: {e}")
        return jsonify({'error': str(e)}), 500

def process_kol_track_signal(message_text: str, message_id: str) -> dict:
    """
    معالجة إشارة شراء جديدة من KOL Track
    """
    try:
        # استخلاص بيانات الإشارة
        signal_data = analyzer.extract_kol_track_data(message_text)
        if not signal_data:
            return {'error': 'فشل في استخلاص بيانات الإشارة'}
        
        # إنشاء معرف فريد للإشارة
        signal_id = f"signal_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{message_id[:8]}"
        
        # جلب بيانات أداء المحافظ
        wallets_performance = []
        for wallet_info in signal_data['wallets_details']:
            wallet_unique_id = f"{wallet_info['type']}_{wallet_info['id']}"
            wallet = Wallet.query.filter_by(wallet_unique_id=wallet_unique_id).first()
            if wallet:
                wallets_performance.append(wallet.to_dict())
        
        # حساب درجة الثقة
        participating_wallets = [f"{w['type']}_{w['id']}" for w in signal_data['wallets_details']]
        score, decision, reasons = analyzer.calculate_confidence_score(participating_wallets, wallets_performance)
        
        # حفظ الإشارة في قاعدة البيانات
        signal = Signal(
            signal_id=signal_id,
            contract_address=signal_data['contract_address'],
            signal_time=datetime.now(timezone.utc),
            token_name=signal_data['token_name'],
            total_wallets_involved=signal_data['total_wallets_involved'],
            wallets_details=json.dumps(signal_data['wallets_details']),
            decision=decision,
            confidence_score=score,
            decision_reasons=json.dumps(reasons),
            performance_status='PENDING',
            evaluation_complete=False
        )
        db.session.add(signal)
        
        # حفظ روابط المحافظ
        for wallet_info in signal_data['wallets_details']:
            wallet_unique_id = f"{wallet_info['type']}_{wallet_info['id']}"
            link_id = f"link_{signal_id}_{wallet_unique_id}"
            
            link = SignalWalletLink(
                link_id=link_id,
                signal_id=signal_id,
                wallet_unique_id=wallet_unique_id,
                mc_at_buy=wallet_info['mc_at_buy']
            )
            db.session.add(link)
            
            # تحديث إحصائيات المحفظة
            wallet = Wallet.query.filter_by(wallet_unique_id=wallet_unique_id).first()
            if wallet:
                wallet.total_calls += 1
                wallet.last_seen = datetime.now(timezone.utc)
            else:
                # إنشاء محفظة جديدة
                new_wallet = Wallet(
                    wallet_unique_id=wallet_unique_id,
                    wallet_type=wallet_info['type'],
                    wallet_number=wallet_info['id'],
                    date_added=datetime.now(timezone.utc),
                    last_seen=datetime.now(timezone.utc),
                    total_calls=1,
                    successful_calls=0,
                    success_rate=0.0
                )
                db.session.add(new_wallet)
        
        db.session.commit()
        
        # إرسال التوصية إذا كان القرار إيجابياً
        result = {
            'signal_id': signal_id,
            'decision': decision,
            'score': score,
            'reasons': reasons,
            'contract_address': signal_data['contract_address'],
            'token_name': signal_data['token_name']
        }
        
        if decision in ['BUY', 'STRONG_BUY']:
            # إرسال الرسالة إلى تيليجرام
            try:
                success = telegram_service.send_message_sync(
                    analyzer.format_decision_message(
                        decision, signal_data['token_name'], 
                        signal_data['contract_address'], score, reasons
                    )
                )
                result['recommendation_sent'] = success
                result['message'] = analyzer.format_decision_message(
                    decision, signal_data['token_name'], 
                    signal_data['contract_address'], score, reasons
                )
            except Exception as e:
                logging.error(f"خطأ في إرسال الإشعار: {e}")
                result['recommendation_sent'] = False
        
        return result
        
    except Exception as e:
        logging.error(f"خطأ في معالجة إشارة KOL Track: {e}")
        return {'error': str(e)}

def process_phanes_update(message_text: str, signal_type: str) -> dict:
    """
    معالجة تحديث Phanes لتقييم أداء الإشارات
    """
    try:
        # استخلاص بيانات Phanes
        phanes_data = analyzer.extract_phanes_data(message_text)
        if not phanes_data:
            return {'error': 'فشل في استخلاص بيانات Phanes'}
        
        contract_address = phanes_data['contract_address']
        current_ath = phanes_data['ath_usd']
        
        # البحث عن الإشارة الأصلية
        signal = Signal.query.filter_by(
            contract_address=contract_address,
            evaluation_complete=False
        ).first()
        
        if not signal:
            return {'message': 'لم يتم العثور على إشارة مطابقة'}
        
        # تحديث ATH الأولي إذا لم يكن محدداً
        if signal.initial_ath_usd == 0.0:
            signal.initial_ath_usd = current_ath
            db.session.commit()
            return {'message': 'تم تحديث ATH الأولي', 'initial_ath': current_ath}
        
        # تقييم الأداء
        performance_status, evaluation_complete = analyzer.evaluate_signal_performance(
            signal.initial_ath_usd, current_ath, signal.signal_time
        )
        
        # تحديث الإشارة
        signal.final_ath_usd = current_ath
        signal.performance_status = performance_status
        signal.evaluation_complete = evaluation_complete
        
        if signal.initial_ath_usd > 0:
            signal.profit_multiplier = current_ath / signal.initial_ath_usd
        
        # تحديث إحصائيات المحافظ في حالة النجاح
        if performance_status == 'SUCCESS' and evaluation_complete:
            links = SignalWalletLink.query.filter_by(signal_id=signal.signal_id).all()
            for link in links:
                wallet = Wallet.query.filter_by(wallet_unique_id=link.wallet_unique_id).first()
                if wallet:
                    wallet.successful_calls += 1
                    wallet.success_rate = wallet.successful_calls / wallet.total_calls if wallet.total_calls > 0 else 0
        
        db.session.commit()
        
        return {
            'signal_id': signal.signal_id,
            'performance_status': performance_status,
            'evaluation_complete': evaluation_complete,
            'initial_ath': signal.initial_ath_usd,
            'current_ath': current_ath,
            'profit_multiplier': signal.profit_multiplier
        }
        
    except Exception as e:
        logging.error(f"خطأ في معالجة تحديث Phanes: {e}")
        return {'error': str(e)}

@smart_falcon_bp.route('/api/signals', methods=['GET'])
def get_signals():
    """
    جلب قائمة الإشارات
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status')
        
        query = Signal.query
        if status:
            query = query.filter_by(performance_status=status)
        
        signals = query.order_by(Signal.signal_time.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'signals': [signal.to_dict() for signal in signals.items],
            'total': signals.total,
            'pages': signals.pages,
            'current_page': page
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@smart_falcon_bp.route('/api/wallets', methods=['GET'])
def get_wallets():
    """
    جلب قائمة المحافظ
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        sort_by = request.args.get('sort_by', 'success_rate')
        
        if sort_by == 'success_rate':
            query = Wallet.query.order_by(Wallet.success_rate.desc())
        elif sort_by == 'total_calls':
            query = Wallet.query.order_by(Wallet.total_calls.desc())
        else:
            query = Wallet.query.order_by(Wallet.last_seen.desc())
        
        wallets = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'wallets': [wallet.to_dict() for wallet in wallets.items],
            'total': wallets.total,
            'pages': wallets.pages,
            'current_page': page
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@smart_falcon_bp.route('/api/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    """
    جلب إحصائيات لوحة التحكم
    """
    try:
        # إحصائيات عامة
        total_signals = Signal.query.count()
        successful_signals = Signal.query.filter_by(performance_status='SUCCESS').count()
        pending_signals = Signal.query.filter_by(performance_status='PENDING').count()
        total_wallets = Wallet.query.count()
        
        # أفضل المحافظ
        top_wallets = Wallet.query.filter(Wallet.total_calls >= 5).order_by(
            Wallet.success_rate.desc()
        ).limit(10).all()
        
        # الإشارات الأخيرة
        recent_signals = Signal.query.order_by(
            Signal.signal_time.desc()
        ).limit(5).all()
        
        return jsonify({
            'stats': {
                'total_signals': total_signals,
                'successful_signals': successful_signals,
                'pending_signals': pending_signals,
                'total_wallets': total_wallets,
                'success_rate': (successful_signals / total_signals * 100) if total_signals > 0 else 0
            },
            'top_wallets': [wallet.to_dict() for wallet in top_wallets],
            'recent_signals': [signal.to_dict() for signal in recent_signals]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@smart_falcon_bp.route('/api/config', methods=['GET', 'POST'])
def system_config():
    """
    إدارة إعدادات النظام
    """
    try:
        if request.method == 'GET':
            configs = SystemConfig.query.all()
            return jsonify({
                'configs': [config.to_dict() for config in configs]
            })
        
        elif request.method == 'POST':
            data = request.get_json()
            config_key = data.get('config_key')
            config_value = data.get('config_value')
            description = data.get('description', '')
            
            if not config_key or not config_value:
                return jsonify({'error': 'بيانات ناقصة'}), 400
            
            # البحث عن الإعداد الموجود أو إنشاء جديد
            config = SystemConfig.query.filter_by(config_key=config_key).first()
            if config:
                config.config_value = config_value
                config.description = description
                config.updated_at = datetime.now(timezone.utc)
            else:
                config = SystemConfig(
                    config_key=config_key,
                    config_value=config_value,
                    description=description
                )
                db.session.add(config)
            
            db.session.commit()
            return jsonify({'message': 'تم حفظ الإعداد بنجاح'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

