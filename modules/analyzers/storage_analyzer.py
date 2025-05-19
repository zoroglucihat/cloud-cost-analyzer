"""
Storage hesapları için analiz modülü.
"""

import logging
from modules.analyzers.resource_analyzer import ResourceAnalyzer

logger = logging.getLogger("StorageAnalyzer")

class StorageAnalyzer(ResourceAnalyzer):
    """
    Storage hesaplarını analiz eden sınıf.
    """
    
    def __init__(self, azure_client, config):
        """
        Storage analizörünü başlatır.
        
        Args:
            azure_client: Azure istemcisi
            config: Uygulama yapılandırması
        """
        super().__init__(azure_client, config)
        self.resource_type_name = "Storage Account"
    
    def analyze(self):
        """
        Storage hesaplarını analiz eder.
        
        Returns:
            İnaktif storage hesaplarının listesi
        """
        logger.info("Storage hesapları analiz ediliyor...")
        inactive_storages = []
        
        try:
            # Tüm storage hesaplarını listele
            storage_accounts = list(self.azure_client.storage_client.storage_accounts.list())
            
            for storage in storage_accounts:
                # İşlem metriklerini al
                transactions = self.azure_client.get_resource_metric(
                    storage.id,
                    'Transactions',
                    self.config.start_time,
                    self.config.end_time,
                    aggregation="Total"  # Toplam işlem sayısı
                )
                
                # İnaktif mi kontrol et
                is_inactive = False
                inactive_reason = ""
                
                if not transactions or self.is_metric_inactive(
                    transactions, self.config.metric_thresholds['storage_transactions_threshold']):
                    is_inactive = True
                    inactive_reason = "Düşük erişim aktivitesi"
                
                if is_inactive:
                    sku_name = storage.sku.name if hasattr(storage, 'sku') and storage.sku else "Unknown"
                    
                    inactive_storages.append(self.create_resource_entry(
                        storage, 'Available', inactive_reason, sku_name
                    ))
            
            logger.info(f"{len(inactive_storages)} inaktif storage hesabı bulundu.")
            return inactive_storages
            
        except Exception as e:
            logger.error(f"Storage hesapları analiz edilirken hata oluştu: {str(e)}")
            return [] 