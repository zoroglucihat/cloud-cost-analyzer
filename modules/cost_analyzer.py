"""
Azure kaynakları için maliyet analizi modülü.
"""

import logging
from datetime import datetime

logger = logging.getLogger("CostAnalyzer")

class CostAnalyzer:
    """
    Azure kaynaklarının maliyetlerini analiz eden sınıf.
    """
    
    def __init__(self, azure_client, config):
        """
        Maliyet analizörünü başlatır.
        
        Args:
            azure_client: Azure istemcisi
            config: Uygulama yapılandırması
        """
        self.azure_client = azure_client
        self.config = config
        
    def get_high_cost_resources(self):
        """
        Yüksek maliyetli kaynakları belirler.
        
        Returns:
            Yüksek maliyetli kaynaklar listesi
        """
        logger.info("Yüksek maliyetli kaynaklar analiz ediliyor...")
        high_cost_resources = []
        
        try:
            # Son fatura döneminin maliyet verilerini al
            usage_details = list(self.azure_client.consumption_client.usage_details.list(
                scope=f"/subscriptions/{self.azure_client.subscription_id}",
                filter=f"properties/usageStart ge '{self.config.cost_start_date}' and properties/usageEnd le '{self.config.cost_end_date}'"
            ))
            
            # Kaynak ID'sine göre maliyetleri grupla
            resource_costs = {}
            
            for usage in usage_details:
                if not usage.resource_id:
                    continue  # Kaynak ID'si olmayan öğeleri atla
                
                resource_id = usage.resource_id.lower()
                cost = usage.pretax_cost or 0
                
                if resource_id not in resource_costs:
                    resource_costs[resource_id] = {
                        'id': usage.resource_id,
                        'name': usage.resource_name or 'Unknown',
                        'type': usage.resource_type or 'Unknown',
                        'resource_group': usage.resource_group or 'Unknown',
                        'location': usage.resource_location or 'Unknown',
                        'cost': 0,
                        'currency': usage.billing_currency or 'USD'
                    }
                
                resource_costs[resource_id]['cost'] += cost
            
            # Maliyet eşiğini aşan kaynakları belirle
            threshold = self.config.cost_threshold
            for resource_id, resource in resource_costs.items():
                if resource['cost'] >= threshold:
                    high_cost_resources.append(resource)
            
            # Maliyete göre azalan sıralama
            high_cost_resources.sort(key=lambda x: x['cost'], reverse=True)
            
            logger.info(f"{len(high_cost_resources)} yüksek maliyetli kaynak bulundu.")
            return high_cost_resources
            
        except Exception as e:
            logger.error(f"Maliyet verileri alınırken hata oluştu: {str(e)}")
            return []
    
    def add_costs_to_resources(self, resources):
        """
        Kaynak listesine maliyet verilerini ekler.
        
        Args:
            resources: Kaynak listesi (referans ile güncellenecek)
        """
        if not resources:
            return
        
        try:
            # Maliyet verilerini al
            usage_details = list(self.azure_client.consumption_client.usage_details.list(
                scope=f"/subscriptions/{self.azure_client.subscription_id}",
                filter=f"properties/usageStart ge '{self.config.cost_start_date}' and properties/usageEnd le '{self.config.cost_end_date}'"
            ))
            
            # Kaynak ID'sine göre maliyet verileri sözlüğü oluştur
            cost_dict = {}
            for usage in usage_details:
                if not usage.resource_id:
                    continue
                
                resource_id = usage.resource_id.lower()
                cost = usage.pretax_cost or 0
                
                if resource_id not in cost_dict:
                    cost_dict[resource_id] = 0
                
                cost_dict[resource_id] += cost
            
            # Kaynak listesine maliyet verilerini ekle
            for resource in resources:
                resource_id = resource['id'].lower()
                resource['cost'] = cost_dict.get(resource_id, 0)
            
            logger.info(f"{len(resources)} kaynağa maliyet verileri eklendi.")
            
        except Exception as e:
            logger.error(f"Kaynaklara maliyet verileri eklenirken hata oluştu: {str(e)}") 