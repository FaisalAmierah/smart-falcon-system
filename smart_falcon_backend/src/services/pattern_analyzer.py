import pandas as pd
import itertools
import logging
from typing import Dict, List, Tuple, Optional
from src.models.user import db
from src.models.smart_falcon import Wallet, Signal, SignalWalletLink
from datetime import datetime, timedelta
import json

logging.basicConfig(level=logging.INFO)

class AdvancedPatternAnalyzer:
    """
    محلل الأنماط المتقدم لنظام الصقر الذكي
    يقوم بتحليل الأنماط التاريخية واستخلاص القواعد الذكية
    """
    
    def __init__(self):
        self.golden_patterns = {
            'trio': ["KOL_1", "KOL_15", "KOL_22"],
            'pairs': [
                ["New Wallet_56", "New Wallet_82"],
                ["KOL_15", "KOL_22"]
            ]
        }
        
        # عتبات التحليل
        self.MIN_OCCURRENCES = 3
        self.MIN_SUCCESS_RATE = 0.6
        self.HIGH_PERFORMANCE_THRESHOLD = 0.7
        self.LOW_PERFORMANCE_THRESHOLD = 0.15
    
    def analyze_wallet_clusters(self, cluster_size: int = 2) -> Dict:
        """
        تحليل مجموعات المحافظ التي تشتري معاً
        """
        try:
            # جلب البيانات من قاعدة البيانات
            signals_data = self._get_signals_with_wallets()
            
            if not signals_data:
                return {'error': 'لا توجد بيانات كافية للتحليل'}
            
            cluster_performance = {}
            
            # تحليل كل إشارة
            for signal in signals_data:
                wallets = sorted(signal['wallets'])
                if len(wallets) >= cluster_size:
                    # إنشاء كل التوافيق الممكنة
                    for cluster in itertools.combinations(wallets, cluster_size):
                        cluster_key = tuple(sorted(cluster))
                        
                        if cluster_key not in cluster_performance:
                            cluster_performance[cluster_key] = {
                                'total_calls': 0,
                                'successful_calls': 0,
                                'signals': []
                            }
                        
                        cluster_performance[cluster_key]['total_calls'] += 1
                        cluster_performance[cluster_key]['signals'].append(signal['signal_id'])
                        
                        if signal['performance_status'] == 'SUCCESS':
                            cluster_performance[cluster_key]['successful_calls'] += 1
            
            # تحليل النتائج
            promising_clusters = []
            for cluster, data in cluster_performance.items():
                if data['total_calls'] >= self.MIN_OCCURRENCES:
                    success_rate = data['successful_calls'] / data['total_calls']
                    if success_rate >= self.MIN_SUCCESS_RATE:
                        promising_clusters.append({
                            'cluster': list(cluster),
                            'cluster_name': ' & '.join(cluster),
                            'total_calls': data['total_calls'],
                            'successful_calls': data['successful_calls'],
                            'success_rate': success_rate,
                            'signals': data['signals']
                        })
            
            # ترتيب حسب الأداء
            promising_clusters.sort(key=lambda x: (x['success_rate'], x['total_calls']), reverse=True)
            
            return {
                'cluster_size': cluster_size,
                'total_clusters_analyzed': len(cluster_performance),
                'promising_clusters': promising_clusters[:10],  # أفضل 10
                'analysis_summary': {
                    'clusters_with_min_occurrences': len([c for c in cluster_performance.values() if c['total_calls'] >= self.MIN_OCCURRENCES]),
                    'high_performance_clusters': len(promising_clusters)
                }
            }
            
        except Exception as e:
            logging.error(f"خطأ في تحليل مجموعات المحافظ: {e}")
            return {'error': str(e)}
    
    def analyze_individual_performance(self) -> Dict:
        """
        تحليل أداء المحافظ الفردية
        """
        try:
            wallets = Wallet.query.filter(Wallet.total_calls >= 5).all()
            
            performance_categories = {
                'high_performers': [],
                'consistent_performers': [],
                'low_performers': [],
                'new_promising': []
            }
            
            for wallet in wallets:
                wallet_data = wallet.to_dict()
                
                if wallet.success_rate >= self.HIGH_PERFORMANCE_THRESHOLD:
                    performance_categories['high_performers'].append(wallet_data)
                elif wallet.success_rate >= 0.4 and wallet.total_calls >= 10:
                    performance_categories['consistent_performers'].append(wallet_data)
                elif wallet.success_rate <= self.LOW_PERFORMANCE_THRESHOLD and wallet.total_calls > 5:
                    performance_categories['low_performers'].append(wallet_data)
                elif wallet.total_calls <= 10 and wallet.success_rate >= 0.5:
                    performance_categories['new_promising'].append(wallet_data)
            
            # ترتيب كل فئة
            for category in performance_categories:
                performance_categories[category].sort(
                    key=lambda x: (x['success_rate'], x['total_calls']), 
                    reverse=True
                )
            
            return {
                'total_wallets_analyzed': len(wallets),
                'performance_categories': performance_categories,
                'summary': {
                    'high_performers_count': len(performance_categories['high_performers']),
                    'consistent_performers_count': len(performance_categories['consistent_performers']),
                    'low_performers_count': len(performance_categories['low_performers']),
                    'new_promising_count': len(performance_categories['new_promising'])
                }
            }
            
        except Exception as e:
            logging.error(f"خطأ في تحليل الأداء الفردي: {e}")
            return {'error': str(e)}
    
    def analyze_time_patterns(self) -> Dict:
        """
        تحليل الأنماط الزمنية للإشارات
        """
        try:
            signals = Signal.query.filter(Signal.evaluation_complete == True).all()
            
            time_analysis = {
                'hourly_performance': {},
                'daily_performance': {},
                'success_time_distribution': []
            }
            
            for signal in signals:
                if signal.signal_time:
                    hour = signal.signal_time.hour
                    day = signal.signal_time.strftime('%A')
                    
                    # تحليل الأداء بالساعة
                    if hour not in time_analysis['hourly_performance']:
                        time_analysis['hourly_performance'][hour] = {
                            'total': 0, 'successful': 0
                        }
                    
                    time_analysis['hourly_performance'][hour]['total'] += 1
                    if signal.performance_status == 'SUCCESS':
                        time_analysis['hourly_performance'][hour]['successful'] += 1
                    
                    # تحليل الأداء بالأيام
                    if day not in time_analysis['daily_performance']:
                        time_analysis['daily_performance'][day] = {
                            'total': 0, 'successful': 0
                        }
                    
                    time_analysis['daily_performance'][day]['total'] += 1
                    if signal.performance_status == 'SUCCESS':
                        time_analysis['daily_performance'][day]['successful'] += 1
            
            # حساب معدلات النجاح
            for hour_data in time_analysis['hourly_performance'].values():
                hour_data['success_rate'] = hour_data['successful'] / hour_data['total'] if hour_data['total'] > 0 else 0
            
            for day_data in time_analysis['daily_performance'].values():
                day_data['success_rate'] = day_data['successful'] / day_data['total'] if day_data['total'] > 0 else 0
            
            return time_analysis
            
        except Exception as e:
            logging.error(f"خطأ في تحليل الأنماط الزمنية: {e}")
            return {'error': str(e)}
    
    def generate_smart_rules(self) -> Dict:
        """
        توليد القواعد الذكية بناءً على التحليل
        """
        try:
            rules = {
                'cluster_rules': [],
                'individual_rules': [],
                'time_rules': [],
                'confidence_scoring': {}
            }
            
            # قواعد المجموعات
            cluster_analysis = self.analyze_wallet_clusters(2)
            if 'promising_clusters' in cluster_analysis:
                for cluster in cluster_analysis['promising_clusters'][:5]:
                    rules['cluster_rules'].append({
                        'rule_type': 'cluster_bonus',
                        'wallets': cluster['cluster'],
                        'bonus_points': min(50, int(cluster['success_rate'] * 100)),
                        'confidence': cluster['success_rate'],
                        'description': f"مكافأة للمجموعة {cluster['cluster_name']} (نسبة نجاح: {cluster['success_rate']:.1%})"
                    })
            
            # قواعد المحافظ الفردية
            individual_analysis = self.analyze_individual_performance()
            if 'performance_categories' in individual_analysis:
                # المحافظ عالية الأداء
                for wallet in individual_analysis['performance_categories']['high_performers'][:10]:
                    rules['individual_rules'].append({
                        'rule_type': 'high_performer_bonus',
                        'wallet_id': wallet['wallet_unique_id'],
                        'bonus_points': 15,
                        'confidence': wallet['success_rate'],
                        'description': f"مكافأة للمحفظة عالية الأداء {wallet['wallet_unique_id']}"
                    })
                
                # المحافظ ضعيفة الأداء
                for wallet in individual_analysis['performance_categories']['low_performers']:
                    rules['individual_rules'].append({
                        'rule_type': 'low_performer_penalty',
                        'wallet_id': wallet['wallet_unique_id'],
                        'penalty_points': -20,
                        'confidence': 1 - wallet['success_rate'],
                        'description': f"عقوبة للمحفظة ضعيفة الأداء {wallet['wallet_unique_id']}"
                    })
            
            # قواعد نظام النقاط
            rules['confidence_scoring'] = {
                'strong_buy_threshold': 45,
                'buy_threshold': 20,
                'ignore_threshold': 0,
                'golden_trio_bonus': 50,
                'golden_pair_bonus': 35,
                'high_performer_bonus': 15,
                'low_performer_penalty': -20,
                'participation_bonus': 2
            }
            
            return rules
            
        except Exception as e:
            logging.error(f"خطأ في توليد القواعد الذكية: {e}")
            return {'error': str(e)}
    
    def _get_signals_with_wallets(self) -> List[Dict]:
        """
        جلب الإشارات مع المحافظ المرتبطة بها
        """
        try:
            query = db.session.query(
                Signal.signal_id,
                Signal.performance_status,
                SignalWalletLink.wallet_unique_id
            ).join(
                SignalWalletLink, Signal.signal_id == SignalWalletLink.signal_id
            ).filter(
                Signal.evaluation_complete == True
            ).all()
            
            # تجميع البيانات
            signals_dict = {}
            for row in query:
                signal_id = row.signal_id
                if signal_id not in signals_dict:
                    signals_dict[signal_id] = {
                        'signal_id': signal_id,
                        'performance_status': row.performance_status,
                        'wallets': []
                    }
                signals_dict[signal_id]['wallets'].append(row.wallet_unique_id)
            
            return list(signals_dict.values())
            
        except Exception as e:
            logging.error(f"خطأ في جلب بيانات الإشارات: {e}")
            return []
    
    def get_pattern_insights(self) -> Dict:
        """
        الحصول على رؤى شاملة للأنماط
        """
        try:
            insights = {
                'cluster_analysis': self.analyze_wallet_clusters(2),
                'trio_analysis': self.analyze_wallet_clusters(3),
                'individual_performance': self.analyze_individual_performance(),
                'time_patterns': self.analyze_time_patterns(),
                'smart_rules': self.generate_smart_rules()
            }
            
            return insights
            
        except Exception as e:
            logging.error(f"خطأ في الحصول على رؤى الأنماط: {e}")
            return {'error': str(e)}

