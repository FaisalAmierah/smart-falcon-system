from flask import Blueprint, request, jsonify
from src.models.user import db
from src.models.smart_falcon import SystemConfig
from src.models.notifications import NotificationMessage
from src.services.telegram_service import telegram_service
from datetime import datetime, timezone
import json
import logging

notifications_bp = Blueprint('notifications', __name__)

@notifications_bp.route('/api/notifications/send', methods=['POST'])
def send_notification():
    """
    إرسال إشعار مخصص
    """
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({'error': 'الرسالة مطلوبة'}), 400
        
        message = data['message']
        notification_type = data.get('type', 'info')
        
        # إرسال الإشعار
        success = telegram_service.send_message_sync(message)
        
        # حفظ الرسالة في قاعدة البيانات
        notification_msg = NotificationMessage(
            message_text=message,
            message_type='notification',
            sent_successfully=success,
            timestamp=datetime.now(timezone.utc)
        )
        
        db.session.add(notification_msg)
        db.session.commit()
        
        return jsonify({
            'status': 'success' if success else 'failed',
            'message': 'تم إرسال الإشعار بنجاح' if success else 'فشل في إرسال الإشعار',
            'notification_id': notification_msg.id
        })
        
    except Exception as e:
        logging.error(f"خطأ في إرسال الإشعار: {e}")
        return jsonify({'error': str(e)}), 500

@notifications_bp.route('/api/notifications/history', methods=['GET'])
def get_notification_history():
    """
    جلب تاريخ الإشعارات
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        notifications = NotificationMessage.query.order_by(
            NotificationMessage.timestamp.desc()
        ).paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        return jsonify({
            'notifications': [msg.to_dict() for msg in notifications.items],
            'total': notifications.total,
            'pages': notifications.pages,
            'current_page': page,
            'per_page': per_page
        })
        
    except Exception as e:
        logging.error(f"خطأ في جلب تاريخ الإشعارات: {e}")
        return jsonify({'error': str(e)}), 500

@notifications_bp.route('/api/notifications/settings', methods=['GET'])
def get_notification_settings():
    """
    جلب إعدادات الإشعارات
    """
    try:
        settings = {}
        
        # جلب الإعدادات من قاعدة البيانات
        configs = SystemConfig.query.filter(
            SystemConfig.config_key.like('notification_%')
        ).all()
        
        for config in configs:
            settings[config.config_key] = config.config_value
        
        # الإعدادات الافتراضية
        default_settings = {
            'notification_enabled': True,
            'notification_strong_buy_only': False,
            'notification_include_analysis': True,
            'notification_channel_id': '',
            'notification_bot_token': ''
        }
        
        # دمج الإعدادات
        for key, default_value in default_settings.items():
            if key not in settings:
                settings[key] = default_value
        
        return jsonify(settings)
        
    except Exception as e:
        logging.error(f"خطأ في جلب إعدادات الإشعارات: {e}")
        return jsonify({'error': str(e)}), 500

@notifications_bp.route('/api/notifications/settings', methods=['POST'])
def update_notification_settings():
    """
    تحديث إعدادات الإشعارات
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'البيانات مطلوبة'}), 400
        
        # تحديث الإعدادات
        for key, value in data.items():
            if key.startswith('notification_'):
                config = SystemConfig.query.filter_by(config_key=key).first()
                
                if config:
                    config.config_value = value
                    config.updated_at = datetime.now(timezone.utc)
                else:
                    config = SystemConfig(
                        config_key=key,
                        config_value=value,
                        created_at=datetime.now(timezone.utc),
                        updated_at=datetime.now(timezone.utc)
                    )
                    db.session.add(config)
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'تم تحديث الإعدادات بنجاح'
        })
        
    except Exception as e:
        logging.error(f"خطأ في تحديث إعدادات الإشعارات: {e}")
        return jsonify({'error': str(e)}), 500

@notifications_bp.route('/api/notifications/test', methods=['POST'])
def test_notification():
    """
    اختبار إرسال الإشعارات
    """
    try:
        test_message = """
🧪 **رسالة اختبار من الصقر الذكي**

هذه رسالة اختبار للتأكد من عمل نظام الإشعارات بشكل صحيح.

⏰ **الوقت:** {time}

#SmartFalcon #Test
        """.format(time=datetime.now().strftime('%Y-%m-%d %H:%M:%S')).strip()
        
        success = telegram_service.send_message_sync(test_message)
        
        # حفظ رسالة الاختبار
        notification_msg = NotificationMessage(
            message_text=test_message,
            message_type='test',
            sent_successfully=success,
            timestamp=datetime.now(timezone.utc)
        )
        
        db.session.add(notification_msg)
        db.session.commit()
        
        return jsonify({
            'status': 'success' if success else 'failed',
            'message': 'تم إرسال رسالة الاختبار بنجاح' if success else 'فشل في إرسال رسالة الاختبار',
            'test_message_id': notification_msg.id
        })
        
    except Exception as e:
        logging.error(f"خطأ في اختبار الإشعارات: {e}")
        return jsonify({'error': str(e)}), 500

@notifications_bp.route('/api/notifications/stats', methods=['GET'])
def get_notification_stats():
    """
    إحصائيات الإشعارات
    """
    try:
        # إجمالي الرسائل
        total_messages = NotificationMessage.query.count()
        
        # الرسائل الناجحة
        successful_messages = NotificationMessage.query.filter_by(sent_successfully=True).count()
        
        # الرسائل الفاشلة
        failed_messages = NotificationMessage.query.filter_by(sent_successfully=False).count()
        
        # الرسائل حسب النوع
        message_types = db.session.query(
            NotificationMessage.message_type,
            db.func.count(NotificationMessage.id).label('count')
        ).group_by(NotificationMessage.message_type).all()
        
        type_stats = {msg_type: count for msg_type, count in message_types}
        
        # معدل النجاح
        success_rate = (successful_messages / total_messages * 100) if total_messages > 0 else 0
        
        return jsonify({
            'total_messages': total_messages,
            'successful_messages': successful_messages,
            'failed_messages': failed_messages,
            'success_rate': round(success_rate, 2),
            'message_types': type_stats
        })
        
    except Exception as e:
        logging.error(f"خطأ في جلب إحصائيات الإشعارات: {e}")
        return jsonify({'error': str(e)}), 500

