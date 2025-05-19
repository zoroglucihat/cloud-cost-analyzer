"""
Azure Cost Optimizer için yapılandırma modülü.
"""

import os
from datetime import datetime, timedelta

class AccountConfig:
    """
    Tek bir Azure hesabı için yapılandırma.
    """
    
    def __init__(self, subscription_id, display_name=None, days_inactive=30, cost_threshold=10.0):
        """
        Hesap yapılandırmasını başlatır.
        
        Args:
            subscription_id: Azure Abonelik ID'si
            display_name: Görünen hesap adı
            days_inactive: Bir kaynağın inaktif sayılması için gün sayısı
            cost_threshold: Maliyet uyarısı için eşik değeri (USD)
        """
        self.subscription_id = subscription_id
        self.display_name = display_name or f"Abonelik {subscription_id[-8:]}"
        self.days_inactive = days_inactive
        self.cost_threshold = cost_threshold
        
        # Analiz için tarih aralıkları
        self.end_time = datetime.now()
        self.start_time = self.end_time - timedelta(days=days_inactive)
        
        # Maliyet analizleri için tarih aralıkları
        self.today = datetime.now().date()
        first_day_prev_month = (self.today.replace(day=1) - timedelta(days=1)).replace(day=1)
        self.cost_start_date = first_day_prev_month.strftime('%Y-%m-%d')
        self.cost_end_date = self.today.strftime('%Y-%m-%d')
        
        # Metrik analizi için eşik değerleri
        self.metric_thresholds = {
            'vm_cpu_threshold': 5.0,            # %5 CPU kullanımından az
            'app_service_requests_threshold': 10.0,  # Günde 10 istek veya daha az
            'storage_transactions_threshold': 100.0,  # Günde 100 işlem veya daha az
            'sql_dtu_threshold': 5.0,           # %5 DTU kullanımından az
            'cosmos_requests_threshold': 10.0,   # Günde 10 istek veya daha az
            'aks_cpu_threshold': 10.0           # %10 CPU kullanımından az
        }

class AppConfig:
    """
    Uygulama yapılandırma sınıfı.
    """
    
    def __init__(self, accounts=None, output_dir="reports"):
        """
        Yapılandırma ayarlarını başlatır.
        
        Args:
            accounts: AccountConfig nesnelerinin listesi
            output_dir: Raporların kaydedileceği dizin
        """
        self.accounts = accounts or []
        self.output_dir = output_dir
        
        # Analiz için tarih aralıkları
        self.end_time = datetime.now()
        self.start_time = self.end_time - timedelta(days=30)
        
        # Maliyet analizleri için tarih aralıkları
        self.today = datetime.now().date()
        first_day_prev_month = (self.today.replace(day=1) - timedelta(days=1)).replace(day=1)
        self.cost_start_date = first_day_prev_month.strftime('%Y-%m-%d')
        self.cost_end_date = self.today.strftime('%Y-%m-%d')
        
        # Metrik analizi için eşik değerleri
        self.metric_thresholds = {
            'vm_cpu_threshold': 5.0,            # %5 CPU kullanımından az
            'app_service_requests_threshold': 10.0,  # Günde 10 istek veya daha az
            'storage_transactions_threshold': 100.0,  # Günde 100 işlem veya daha az
            'sql_dtu_threshold': 5.0,           # %5 DTU kullanımından az
            'cosmos_requests_threshold': 10.0,   # Günde 10 istek veya daha az
            'aks_cpu_threshold': 10.0           # %10 CPU kullanımından az
        } 