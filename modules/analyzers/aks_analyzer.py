"""
AKS kümeleri için analiz modülü.
"""

import logging
from modules.analyzers.resource_analyzer import ResourceAnalyzer

logger = logging.getLogger("AKSAnalyzer")

class AKSAnalyzer(ResourceAnalyzer):
    """
    AKS kümelerini analiz eden sınıf.
    """
    
    def __init__(self, azure_client, config):
        """
        AKS analizörünü başlatır.
        
        Args:
            azure_client: Azure istemcisi
            config: Uygulama yapılandırması
        """
        super().__init__(azure_client, config)
        self.resource_type_name = "AKS Cluster"
    
    def analyze(self):
        """
        AKS kümelerini analiz eder.
        
        Returns:
            İnaktif AKS kümelerinin listesi
        """
        logger.info("AKS kümeleri analiz ediliyor...")
        inactive_clusters = []
        
        try:
            # Tüm AKS kümelerini listele
            aks_clusters = list(self.azure_client.aks_client.managed_clusters.list())
            
            for cluster in aks_clusters:
                # Node CPU kullanım metriklerini al
                node_cpu = self.azure_client.get_resource_metric(
                    cluster.id,
                    'node_cpu_usage_percentage',
                    self.config.start_time,
                    self.config.end_time
                )
                
                # İnaktif mi kontrol et
                is_inactive = False
                inactive_reason = ""
                
                if not node_cpu or self.is_metric_inactive(
                    node_cpu, self.config.metric_thresholds['aks_cpu_threshold']):
                    is_inactive = True
                    inactive_reason = "Düşük CPU kullanımı"
                
                if is_inactive:
                    # Node sayısını hesapla
                    node_count = sum(pool.count for pool in cluster.agent_pool_profiles) if cluster.agent_pool_profiles else 0
                    size_info = f"{node_count} node"
                    
                    inactive_clusters.append(self.create_resource_entry(
                        cluster, cluster.provisioning_state, inactive_reason, size_info
                    ))
            
            logger.info(f"{len(inactive_clusters)} inaktif AKS kümesi bulundu.")
            return inactive_clusters
            
        except Exception as e:
            logger.error(f"AKS kümeleri analiz edilirken hata oluştu: {str(e)}")
            return [] 