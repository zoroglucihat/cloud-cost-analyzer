"""
Azure kaynakları için temel analizör sınıfı.
"""

import logging
from abc import ABC, abstractmethod

logger = logging.getLogger("ResourceAnalyzer")

class ResourceAnalyzer(ABC):
    """
    Çeşitli Azure kaynakları için temel analizör sınıfı.
    """
    
    def __init__(self, azure_client, config):
        """
        Temel analizör sınıfını başlatır.
        
        Args:
            azure_client: Azure istemcisi
            config: Uygulama yapılandırması
        """
        self.azure_client = azure_client
        self.config = config
        self.resource_type_name = "Generic Resource" # Alt sınıflar tarafından override edilmeli
    
    @abstractmethod
    def analyze(self):
        """
        Kaynakları analiz eder.
        """
        pass
    
    def is_metric_inactive(self, metric_value, threshold):
        """
        Bir metrik değerinin inaktif olup olmadığını kontrol eder.
        
        Args:
            metric_value: Metrik değeri
            threshold: İnaktiflik eşiği
            
        Returns:
            True ise inaktif, False ise aktif
        """
        return metric_value is None or metric_value < threshold
    
    def create_resource_entry(self, resource, state, reason, size_info=None):
        """
        Kaynak bilgilerini içeren bir sözlük oluşturur.
        
        Args:
            resource: Azure kaynak nesnesi
            state: Kaynağın durumu
            reason: İnaktiflik nedeni
            size_info: Boyut bilgisi (isteğe bağlı)
            
        Returns:
            Kaynak bilgilerini içeren sözlük
        """
        resource_group = self.azure_client.extract_resource_group(resource.id)
        
        return {
            'id': resource.id,
            'name': resource.name,
            'type': self.resource_type_name,
            'resource_group': resource_group,
            'location': resource.location,
            'size': size_info or "Unknown",
            'state': state,
            'reason': reason,
            'cost': 0.0  # Başlangıçta maliyet bilgisi yok, daha sonra CostAnalyzer tarafından doldurulacak
        } 