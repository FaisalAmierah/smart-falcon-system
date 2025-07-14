from flask import Blueprint, request, jsonify
from src.services.pattern_analyzer import AdvancedPatternAnalyzer
from src.models.user import db
from src.models.smart_falcon import Wallet, Signal, SignalWalletLink
import logging

analytics_bp = Blueprint('analytics', __name__)
analyzer = AdvancedPatternAnalyzer()

@analytics_bp.route('/api/analytics/patterns', methods=['GET'])
def get_pattern_insights():
    """
    الحصول على رؤى شاملة للأنماط
    """
    try:
        insights = analyzer.get_pattern_insights()
        return jsonify(insights)
        
    except Exception as e:
        logging.error(f"خطأ في جلب رؤى الأنماط: {e}")
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/api/analytics/clusters', methods=['GET'])
def analyze_clusters():
    """
    تحليل مجموعات المحافظ
    """
    try:
        cluster_size = request.args.get('size', 2, type=int)
        
        if cluster_size < 2 or cluster_size > 5:
            return jsonify({'error': 'حجم المجموعة يجب أن يكون بين 2 و 5'}), 400
        
        analysis = analyzer.analyze_wallet_clusters(cluster_size)
        return jsonify(analysis)
        
    except Exception as e:
        logging.error(f"خطأ في تحليل المجموعات: {e}")
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/api/analytics/performance', methods=['GET'])
def analyze_performance():
    """
    تحليل أداء المحافظ الفردية
    """
    try:
        analysis = analyzer.analyze_individual_performance()
        return jsonify(analysis)
        
    except Exception as e:
        logging.error(f"خطأ في تحليل الأداء: {e}")
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/api/analytics/time-patterns', methods=['GET'])
def analyze_time_patterns():
    """
    تحليل الأنماط الزمنية
    """
    try:
        analysis = analyzer.analyze_time_patterns()
        return jsonify(analysis)
        
    except Exception as e:
        logging.error(f"خطأ في تحليل الأنماط الزمنية: {e}")
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/api/analytics/rules', methods=['GET'])
def get_smart_rules():
    """
    الحصول على القواعد الذكية
    """
    try:
        rules = analyzer.generate_smart_rules()
        return jsonify(rules)
        
    except Exception as e:
        logging.error(f"خطأ في جلب القواعد الذكية: {e}")
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/api/analytics/wallet/<wallet_id>', methods=['GET'])
def get_wallet_analysis(wallet_id):
    """
    تحليل مفصل لمحفظة معينة
    """
    try:
        # جلب بيانات المحفظة
        wallet = Wallet.query.filter_by(wallet_unique_id=wallet_id).first()
        if not wallet:
            return jsonify({'error': 'المحفظة غير موجودة'}), 404
        
        # جلب الإشارات المرتبطة
        links = SignalWalletLink.query.filter_by(wallet_unique_id=wallet_id).all()
        signal_ids = [link.signal_id for link in links]
        
        signals = Signal.query.filter(Signal.signal_id.in_(signal_ids)).all()
        
        # تحليل الأداء
        successful_signals = [s for s in signals if s.performance_status == 'SUCCESS']
        failed_signals = [s for s in signals if s.performance_status == 'FAILURE']
        pending_signals = [s for s in signals if s.performance_status == 'PENDING']
        
        # تحليل الشركاء المتكررين
        partner_analysis = {}
        for signal in signals:
            signal_links = SignalWalletLink.query.filter_by(signal_id=signal.signal_id).all()
            partners = [link.wallet_unique_id for link in signal_links if link.wallet_unique_id != wallet_id]
            
            for partner in partners:
                if partner not in partner_analysis:
                    partner_analysis[partner] = {'total': 0, 'successful': 0}
                partner_analysis[partner]['total'] += 1
                if signal.performance_status == 'SUCCESS':
                    partner_analysis[partner]['successful'] += 1
        
        # حساب معدلات النجاح للشركاء
        for partner_data in partner_analysis.values():
            partner_data['success_rate'] = partner_data['successful'] / partner_data['total'] if partner_data['total'] > 0 else 0
        
        # ترتيب الشركاء حسب الأداء
        top_partners = sorted(
            [(partner, data) for partner, data in partner_analysis.items() if data['total'] >= 3],
            key=lambda x: (x[1]['success_rate'], x[1]['total']),
            reverse=True
        )[:10]
        
        analysis = {
            'wallet_info': wallet.to_dict(),
            'performance_summary': {
                'total_signals': len(signals),
                'successful_signals': len(successful_signals),
                'failed_signals': len(failed_signals),
                'pending_signals': len(pending_signals),
                'success_rate': wallet.success_rate
            },
            'recent_signals': [signal.to_dict() for signal in signals[-10:]],
            'top_partners': [
                {
                    'wallet_id': partner,
                    'collaborations': data['total'],
                    'successful_collaborations': data['successful'],
                    'success_rate': data['success_rate']
                }
                for partner, data in top_partners
            ],
            'performance_trend': {
                'recent_success_rate': len([s for s in signals[-20:] if s.performance_status == 'SUCCESS']) / min(20, len(signals)) if signals else 0,
                'overall_success_rate': wallet.success_rate
            }
        }
        
        return jsonify(analysis)
        
    except Exception as e:
        logging.error(f"خطأ في تحليل المحفظة {wallet_id}: {e}")
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/api/analytics/signal/<signal_id>', methods=['GET'])
def get_signal_analysis(signal_id):
    """
    تحليل مفصل لإشارة معينة
    """
    try:
        # جلب بيانات الإشارة
        signal = Signal.query.filter_by(signal_id=signal_id).first()
        if not signal:
            return jsonify({'error': 'الإشارة غير موجودة'}), 404
        
        # جلب المحافظ المشاركة
        links = SignalWalletLink.query.filter_by(signal_id=signal_id).all()
        wallet_ids = [link.wallet_unique_id for link in links]
        wallets = Wallet.query.filter(Wallet.wallet_unique_id.in_(wallet_ids)).all()
        
        # تحليل المحافظ المشاركة
        participating_wallets = []
        for wallet in wallets:
            wallet_data = wallet.to_dict()
            # إضافة معلومات الشراء
            link = next((l for l in links if l.wallet_unique_id == wallet.wallet_unique_id), None)
            if link:
                wallet_data['mc_at_buy'] = link.mc_at_buy
            participating_wallets.append(wallet_data)
        
        # ترتيب المحافظ حسب الأداء
        participating_wallets.sort(key=lambda x: x['success_rate'], reverse=True)
        
        # تحليل القرار
        decision_analysis = {
            'high_performers': len([w for w in participating_wallets if w['success_rate'] >= 0.7]),
            'low_performers': len([w for w in participating_wallets if w['success_rate'] < 0.15 and w['total_calls'] > 5]),
            'average_success_rate': sum(w['success_rate'] for w in participating_wallets) / len(participating_wallets) if participating_wallets else 0
        }
        
        analysis = {
            'signal_info': signal.to_dict(),
            'participating_wallets': participating_wallets,
            'decision_analysis': decision_analysis,
            'performance_metrics': {
                'profit_multiplier': signal.profit_multiplier,
                'initial_ath': signal.initial_ath_usd,
                'final_ath': signal.final_ath_usd,
                'performance_status': signal.performance_status
            }
        }
        
        return jsonify(analysis)
        
    except Exception as e:
        logging.error(f"خطأ في تحليل الإشارة {signal_id}: {e}")
        return jsonify({'error': str(e)}), 500

