"""
SQL veritabanları için analiz modülü.
"""

import logging
from modules.analyzers.resource_analyzer import ResourceAnalyzer

logger = logging.getLogger("SQLAnalyzer")

class SQLAnalyzer(ResourceAnalyzer):
    """
    SQL veritabanlarını analiz eden sınıf.
    """
    
    def __init__(self, azure_client, config):
        """
        SQL analizörünü başlatır.
        
        Args:
            azure_client: Azure istemcisi
            config: Uygulama yapılandırması
        """
        super().__init__(azure_client, config)
        self.resource_type_name = "SQL Database"
    
    def analyze(self):
        """
        SQL veritabanlarını analiz eder.
        
        Returns:
            İnaktif SQL veritabanlarının listesi
        """
        logger.info("SQL veritabanları analiz ediliyor...")
        inactive_dbs = []
        
        try:
            # Tüm SQL sunucularını listele
            servers = list(self.azure_client.sql_client.servers.list())
            
            for server in servers:
                resource_group = self.azure_client.extract_resource_group(server.id)
                
                # Sunucuya ait veritabanlarını listele
                databases = list(self.azure_client.sql_client.databases.list_by_server(
                    resource_group, server.name))
                
                for db in databases:
                    # Master veritabanını atla
                    if db.name.lower() == 'master':
                        continue
                    
                    # DTU kullanım metriklerini al
                    dtu_usage = self.azure_client.get_resource_metric(
                        db.id,
                        'dtu_consumption_percent',
                        self.config.start_time,
                        self.config.end_time
                    )
                    
                    # İnaktif mi kontrol et
                    is_inactive = False
                    inactive_reason = ""
                    
                    if not dtu_usage or self.is_metric_inactive(
                        dtu_usage, self.config.metric_thresholds['sql_dtu_threshold']):
                        is_inactive = True
                        inactive_reason = "Düşük DTU kullanımı"
                    
                    if is_inactive:
                        sku_name = db.sku.name if hasattr(db, 'sku') and db.sku else "Unknown"
                        db_status = db.status if hasattr(db, 'status') else 'Unknown'
                        
                        inactive_dbs.append(self.create_resource_entry(
                            db, db_status, inactive_reason, sku_name
                        ))
            
            logger.info(f"{len(inactive_dbs)} inaktif SQL veritabanı bulundu.")
            return inactive_dbs
            
        except Exception as e:
            logger.error(f"SQL veritabanları analiz edilirken hata oluştu: {str(e)}")
            return [] 