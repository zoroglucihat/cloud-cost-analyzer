"""
CosmosDB hesapları için analiz modülü.
"""

import logging
from modules.analyzers.resource_analyzer import ResourceAnalyzer

logger = logging.getLogger("CosmosDBAnalyzer")

class CosmosDBAnalyzer(ResourceAnalyzer):
    """
    CosmosDB hesaplarını analiz eden sınıf.
    """
    
    def __init__(self, azure_client, config):
        """
        CosmosDB analizörünü başlatır.
        
        Args:
            azure_client: Azure istemcisi
            config: Uygulama yapılandırması
        """
        super().__init__(azure_client, config)
        self.resource_type_name = "CosmosDB Account"
    
    def analyze(self):
        """
        CosmosDB hesaplarını analiz eder.
        
        Returns:
            İnaktif CosmosDB hesaplarının listesi
        """
        logger.info("CosmosDB hesapları analiz ediliyor...")
        inactive_accounts = []
        
        try:
            # Tüm CosmosDB hesaplarını listele
            cosmos_accounts = list(self.azure_client.cosmosdb_client.database_accounts.list())
            
            for account in cosmos_accounts:
                # İstek metriklerini al
                total_requests = self.azure_client.get_resource_metric(
                    account.id,
                    'TotalRequests',
                    self.config.start_time,
                    self.config.end_time,
                    aggregation="Total"  # Toplam istek sayısı
                )
                
                # İnaktif mi kontrol et
                is_inactive = False
                inactive_reason = ""
                
                if not total_requests or self.is_metric_inactive(
                    total_requests, self.config.metric_thresholds['cosmos_requests_threshold']):
                    is_inactive = True
                    inactive_reason = "Düşük istek sayısı"
                
                if is_inactive:
                    offer_type = account.database_account_offer_type or "Unknown"
                    
                    inactive_accounts.append(self.create_resource_entry(
                        account, 'Available', inactive_reason, offer_type
                    ))
            
            logger.info(f"{len(inactive_accounts)} inaktif CosmosDB hesabı bulundu.")
            return inactive_accounts
            
        except Exception as e:
            logger.error(f"CosmosDB hesapları analiz edilirken hata oluştu: {str(e)}")
            return [] 