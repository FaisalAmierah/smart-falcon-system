import pandas as pd
import json
from datetime import datetime, timezone
from src.models.user import db
from src.models.smart_falcon import Wallet, Signal, SignalWalletLink
from dateutil.parser import parse
import logging

logging.basicConfig(level=logging.INFO)

class DataImporter:
    """
    خدمة استيراد البيانات التاريخية إلى قاعدة البيانات
    """
    
    def __init__(self):
        self.imported_counts = {
            'wallets': 0,
            'signals': 0,
            'links': 0
        }
    
    def import_from_csv_files(self, wallets_file: str, signals_file: str, links_file: str) -> dict:
        """
        استيراد البيانات من ملفات CSV
        """
        try:
            # استيراد المحافظ
            self.import_wallets(wallets_file)
            
            # استيراد الإشارات
            self.import_signals(signals_file)
            
            # استيراد الروابط
            self.import_links(links_file)
            
            db.session.commit()
            
            return {
                'status': 'success',
                'imported_counts': self.imported_counts,
                'message': 'تم استيراد البيانات بنجاح'
            }
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"خطأ في استيراد البيانات: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def import_wallets(self, file_path: str):
        """
        استيراد بيانات المحافظ
        """
        df = pd.read_csv(file_path)
        
        for _, row in df.iterrows():
            # التحقق من وجود المحفظة
            existing_wallet = Wallet.query.filter_by(
                wallet_unique_id=row['wallet_unique_id']
            ).first()
            
            if not existing_wallet:
                wallet = Wallet(
                    wallet_unique_id=row['wallet_unique_id'],
                    wallet_type=row['wallet_type'],
                    wallet_number=int(row['wallet_number']),
                    date_added=self._parse_datetime(row['date_added']),
                    last_seen=self._parse_datetime(row['last_seen']),
                    total_calls=int(row['total_calls']),
                    successful_calls=int(row['successful_calls']),
                    success_rate=float(row['success_rate']),
                    status='ACTIVE'
                )
                db.session.add(wallet)
                self.imported_counts['wallets'] += 1
        
        logging.info(f"تم استيراد {self.imported_counts['wallets']} محفظة")
    
    def import_signals(self, file_path: str):
        """
        استيراد بيانات الإشارات
        """
        df = pd.read_csv(file_path)
        
        for _, row in df.iterrows():
            # التحقق من وجود الإشارة
            existing_signal = Signal.query.filter_by(
                signal_id=f"historical_{row['signal_id']}"
            ).first()
            
            if not existing_signal:
                # تحضير تفاصيل المحافظ
                wallets_details = []
                if pd.notna(row.get('wallets_details')):
                    try:
                        wallets_details = json.loads(row['wallets_details'])
                    except:
                        wallets_details = []
                
                signal = Signal(
                    signal_id=f"historical_{row['signal_id']}",
                    contract_address=row['contract_address'],
                    signal_time=self._parse_datetime(row['signal_timestamp']),
                    token_name=row.get('token_name', 'N/A'),
                    total_wallets_involved=int(row.get('total_wallets_involved', 0)),
                    wallets_details=json.dumps(wallets_details),
                    initial_ath_usd=float(row.get('initial_ath_usd', 0)),
                    final_ath_usd=float(row.get('final_ath_usd', 0)),
                    profit_multiplier=float(row.get('profit_multiplier', 0)),
                    performance_status=row.get('performance_status', 'PENDING'),
                    evaluation_complete=bool(row.get('evaluation_complete', False))
                )
                db.session.add(signal)
                self.imported_counts['signals'] += 1
        
        logging.info(f"تم استيراد {self.imported_counts['signals']} إشارة")
    
    def import_links(self, file_path: str):
        """
        استيراد روابط الإشارات والمحافظ
        """
        df = pd.read_csv(file_path)
        
        for _, row in df.iterrows():
            # التحقق من وجود الرابط
            existing_link = SignalWalletLink.query.filter_by(
                signal_id=f"historical_{row['signal_id']}",
                wallet_unique_id=row['wallet_unique_id']
            ).first()
            
            if not existing_link:
                link = SignalWalletLink(
                    link_id=f"historical_link_{row['signal_id']}_{row['wallet_unique_id']}",
                    signal_id=f"historical_{row['signal_id']}",
                    wallet_unique_id=row['wallet_unique_id'],
                    mc_at_buy=float(row.get('mc_at_buy', 0))
                )
                db.session.add(link)
                self.imported_counts['links'] += 1
        
        logging.info(f"تم استيراد {self.imported_counts['links']} رابط")
    
    def _parse_datetime(self, date_str):
        """
        تحويل النص إلى تاريخ ووقت
        """
        if pd.isna(date_str):
            return datetime.now(timezone.utc)
        
        try:
            # محاولة تحليل التاريخ
            parsed_date = parse(str(date_str))
            if parsed_date.tzinfo is None:
                parsed_date = parsed_date.replace(tzinfo=timezone.utc)
            return parsed_date
        except:
            return datetime.now(timezone.utc)
    
    def clear_all_data(self):
        """
        مسح جميع البيانات من قاعدة البيانات
        """
        try:
            SignalWalletLink.query.delete()
            Signal.query.delete()
            Wallet.query.delete()
            db.session.commit()
            logging.info("تم مسح جميع البيانات")
            return True
        except Exception as e:
            db.session.rollback()
            logging.error(f"خطأ في مسح البيانات: {e}")
            return False
    
    def get_import_status(self):
        """
        جلب حالة الاستيراد
        """
        return {
            'wallets_count': Wallet.query.count(),
            'signals_count': Signal.query.count(),
            'links_count': SignalWalletLink.query.count(),
            'last_imported': self.imported_counts
        }

