from flask import Blueprint, request, jsonify
from src.services.data_importer import DataImporter
import os

data_import_bp = Blueprint('data_import', __name__)

@data_import_bp.route('/api/import/csv', methods=['POST'])
def import_csv_data():
    """
    استيراد البيانات من ملفات CSV
    """
    try:
        data = request.get_json()
        
        # مسارات الملفات
        wallets_file = data.get('wallets_file')
        signals_file = data.get('signals_file')
        links_file = data.get('links_file')
        
        if not all([wallets_file, signals_file, links_file]):
            return jsonify({'error': 'جميع مسارات الملفات مطلوبة'}), 400
        
        # التحقق من وجود الملفات
        for file_path in [wallets_file, signals_file, links_file]:
            if not os.path.exists(file_path):
                return jsonify({'error': f'الملف غير موجود: {file_path}'}), 400
        
        # تنفيذ الاستيراد
        importer = DataImporter()
        result = importer.import_from_csv_files(wallets_file, signals_file, links_file)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@data_import_bp.route('/api/import/status', methods=['GET'])
def get_import_status():
    """
    جلب حالة الاستيراد
    """
    try:
        importer = DataImporter()
        status = importer.get_import_status()
        return jsonify(status)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@data_import_bp.route('/api/import/clear', methods=['POST'])
def clear_data():
    """
    مسح جميع البيانات
    """
    try:
        importer = DataImporter()
        success = importer.clear_all_data()
        
        if success:
            return jsonify({'message': 'تم مسح جميع البيانات بنجاح'})
        else:
            return jsonify({'error': 'فشل في مسح البيانات'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

