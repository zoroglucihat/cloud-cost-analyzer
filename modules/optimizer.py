"""
Azure kaynakları için optimizasyon önerileri modülü.
"""

import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class OptimizationRecommender:
    """
    Azure kaynakları için optimizasyon önerileri üreten sınıf.
    """
    
    def __init__(self, azure_client):
        """
        Optimizasyon önericisini başlatır.
        
        Args:
            azure_client: Azure istemcisi
        """
        self.azure_client = azure_client
    
    def generate_recommendations(self, inactive_resources, high_cost_resources):
        """Ana öneri oluşturma metodu"""
        logger.info("Optimizasyon önerileri oluşturuluyor...")
        
        recommendations = []
        
        # İnaktif kaynaklar için detaylı analiz ve öneriler
        inactive_recommendations = self.analyze_inactive_resources(inactive_resources)
        recommendations.extend(inactive_recommendations)
        
        # Yüksek maliyetli kaynaklar için detaylı analiz ve öneriler
        cost_recommendations = self.analyze_high_cost_resources(high_cost_resources)
        recommendations.extend(cost_recommendations)
        
        logger.info(f"{len(recommendations)} optimizasyon önerisi oluşturuldu.")
        return recommendations
    
    def analyze_inactive_resources(self, inactive_resources):
        """
        İnaktif kaynakları detaylı analiz eder ve öneriler sunar.
        """
        recommendations = []
        
        for resource in inactive_resources:
            resource_type = resource['type'].lower()
            
            # Temel tahmini tasarruf hesaplama (aylık maliyet)
            monthly_cost = resource.get('cost', 0)
            
            # Kaynak türüne özgü öneriler
            if 'microsoft.compute/virtualmachines' in resource_type:
                recommendations.append(self._analyze_inactive_vm(resource, monthly_cost))
            
            elif 'microsoft.storage/storageaccounts' in resource_type:
                recommendations.append(self._analyze_inactive_storage(resource, monthly_cost))
            
            elif 'microsoft.web/sites' in resource_type:
                recommendations.append(self._analyze_inactive_app_service(resource, monthly_cost))
            
            elif 'microsoft.sql/servers/databases' in resource_type:
                recommendations.append(self._analyze_inactive_sql_db(resource, monthly_cost))
            
            elif 'microsoft.documentdb/databaseaccounts' in resource_type:
                recommendations.append(self._analyze_inactive_cosmos_db(resource, monthly_cost))
            
            elif 'microsoft.containerservice/managedclusters' in resource_type:
                recommendations.append(self._analyze_inactive_aks(resource, monthly_cost))
            
            else:
                # Genel inaktif kaynak önerisi
                recommendations.append({
                    'resource_id': resource['id'],
                    'resource_name': resource['name'],
                    'resource_type': resource['type'],
                    'resource_group': resource['resource_group'],
                    'issue': f"Bu kaynak {resource.get('reason', 'bilinmeyen bir nedenle')} inaktif durumdadır.",
                    'cost_impact': monthly_cost,
                    'inactive_days': resource.get('inactive_days', 0),
                    'recommendations': [
                        "Kaynağı devre dışı bırakın",
                        "Gereksizse kaynağı silin",
                        "Kaynağı korumak istiyorsanız, daha düşük maliyetli bir seçeneğe geçin"
                    ],
                    'potential_savings': {
                        'monthly': monthly_cost,
                        'yearly': monthly_cost * 12
                    },
                    'estimated_effort': 'Düşük',
                    'risk_level': 'Düşük',
                    'recommendation_type': 'İnaktif Kaynak'
                })
        
        return recommendations
    
    def _analyze_inactive_vm(self, resource, monthly_cost):
        """
        İnaktif VM'ler için detaylı analiz ve öneriler.
        """
        size = resource.get('size', 'bilinmiyor')
        inactive_days = resource.get('inactive_days', 0)
        reserved_instance = resource.get('reserved_instance', False)
        
        options = []
        if inactive_days > 90:
            options.append("VM'i tamamen silin (3 aydan uzun süredir inaktif)")
        else:
            options.append("VM'i deallocate edin (yalnızca depolama maliyeti ödersiniz)")
        
        if reserved_instance:
            options.append("Reserved Instance satın aldıysanız, başka bir VM'e taşıyın")
        
        if size.lower() in ['standard_d', 'standard_e', 'standard_f']:
            options.append("Daha düşük maliyetli B serisi VM'lere geçiş yapın")
        
        options.append("Start/Stop çizelgesi tanımlayarak çalışma saatlerini optimize edin")
        options.append("Disk türünü Premium'dan Standard'a düşürmeyi değerlendirin")
        
        return {
            'resource_id': resource['id'],
            'resource_name': resource['name'],
            'resource_type': resource['type'],
            'resource_group': resource['resource_group'],
            'issue': f"Bu sanal makine {inactive_days} gündür inaktif durumdadır.",
            'cost_impact': monthly_cost,
            'inactive_days': inactive_days,
            'recommendations': options,
            'potential_savings': {
                'monthly': monthly_cost,
                'yearly': monthly_cost * 12,
                'deallocate_savings': monthly_cost * 0.9  # VM deallocate edilirse yaklaşık %90 tasarruf
            },
            'resource_details': {
                'size': size,
                'disks': resource.get('disks', []),
                'os_type': resource.get('os_type', 'bilinmiyor')
            },
            'estimated_effort': 'Orta',
            'risk_level': 'Düşük',
            'recommendation_type': 'İnaktif VM'
        }
    
    def _analyze_inactive_storage(self, resource, monthly_cost):
        """
        İnaktif storage hesapları için detaylı analiz ve öneriler.
        """
        tier = resource.get('tier', 'bilinmiyor')
        replication = resource.get('replication', 'bilinmiyor')
        
        options = []
        options.append("Boş veya çok az kullanılan konteynerler/blobları temizleyin")
        
        if tier.lower() == 'premium':
            options.append("Standard depolama katmanına geçiş yapın (%60'a kadar tasarruf)")
        
        if replication.lower() in ['grs', 'ra-grs']:
            options.append("Daha düşük yedekleme seviyesine geçin (GRS -> LRS, %50'ye kadar tasarruf)")
        
        options.append("Erişim katmanını Hot'tan Cool/Archive'a değiştirerek maliyeti azaltın")
        
        return {
            'resource_id': resource['id'],
            'resource_name': resource['name'],
            'resource_type': resource['type'],
            'resource_group': resource['resource_group'],
            'issue': f"Bu depolama hesabı aktif olarak kullanılmıyor (son okuma/yazma işlemi: {resource.get('last_access', 'bilinmiyor')})",
            'cost_impact': monthly_cost,
            'recommendations': options,
            'potential_savings': {
                'monthly': monthly_cost,
                'yearly': monthly_cost * 12,
                'tier_change_savings': monthly_cost * 0.6 if tier.lower() == 'premium' else 0
            },
            'resource_details': {
                'tier': tier,
                'replication': replication,
                'access_tier': resource.get('access_tier', 'bilinmiyor')
            },
            'estimated_effort': 'Orta',
            'risk_level': 'Düşük',
            'recommendation_type': 'İnaktif Storage'
        }
    
    # Benzer şekilde diğer kaynak türleri için de analiz fonksiyonları eklenebilir
    def _analyze_inactive_app_service(self, resource, monthly_cost):
        # App Service özgü analiz...
        pass
    
    def _analyze_inactive_sql_db(self, resource, monthly_cost):
        # SQL DB özgü analiz...
        pass
    
    def _analyze_inactive_cosmos_db(self, resource, monthly_cost):
        # CosmosDB özgü analiz...
        pass
    
    def _analyze_inactive_aks(self, resource, monthly_cost):
        # AKS özgü analiz...
        pass
    
    def analyze_high_cost_resources(self, high_cost_resources):
        """
        Yüksek maliyetli kaynakları detaylı analiz eder ve maliyet düşürme önerileri sunar.
        """
        recommendations = []
        
        for resource in high_cost_resources:
            resource_type = resource['type'].lower()
            monthly_cost = resource.get('cost', 0)
            
            # Yüksek maliyetli VM'ler için özel analiz
            if 'microsoft.compute/virtualmachines' in resource_type:
                recommendations.append(self._analyze_high_cost_vm(resource, monthly_cost))
            
            # Storage hesapları için özel analiz
            elif 'microsoft.storage/storageaccounts' in resource_type:
                recommendations.append(self._analyze_high_cost_storage(resource, monthly_cost))
            
            # SQL Veritabanları için özel analiz
            elif 'microsoft.sql/servers/databases' in resource_type:
                recommendations.append(self._analyze_high_cost_sql(resource, monthly_cost))
            
            # CosmosDB hesapları için özel analiz
            elif 'microsoft.documentdb/databaseaccounts' in resource_type:
                recommendations.append(self._analyze_high_cost_cosmos(resource, monthly_cost))
            
            # AKS kümeleri için özel analiz
            elif 'microsoft.containerservice/managedclusters' in resource_type:
                recommendations.append(self._analyze_high_cost_aks(resource, monthly_cost))
            
            # App Service planları için özel analiz
            elif 'microsoft.web/serverfarms' in resource_type:
                recommendations.append(self._analyze_high_cost_app_service_plan(resource, monthly_cost))
            
            # Diğer yüksek maliyetli kaynaklar için genel öneri
            else:
                recommendations.append({
                    'resource_id': resource['id'],
                    'resource_name': resource['name'],
                    'resource_type': resource['type'],
                    'resource_group': resource['resource_group'],
                    'issue': f"Bu kaynak aylık {monthly_cost:.2f} USD maliyeti ile yüksek harcamaya sahip.",
                    'cost_impact': monthly_cost,
                    'recommendations': [
                        "Alternatif fiyatlandırma seçeneklerini değerlendirin",
                        "Kullanım paternlerini analiz ederek optimize edin",
                        "Rezervasyon veya taahhüt planlarını değerlendirin"
                    ],
                    'potential_savings': {
                        'monthly_estimate': monthly_cost * 0.2,  # Tahmini %20 tasarruf
                        'yearly_estimate': monthly_cost * 0.2 * 12
                    },
                    'estimated_effort': 'Orta',
                    'risk_level': 'Orta',
                    'recommendation_type': 'Yüksek Maliyet'
                })
        
        return recommendations
    
    def _analyze_high_cost_vm(self, resource, monthly_cost):
        """
        Yüksek maliyetli VM'ler için detaylı analiz ve maliyet düşürme önerileri.
        """
        size = resource.get('size', 'bilinmiyor')
        cpu_utilization = resource.get('cpu_utilization', 0)
        memory_utilization = resource.get('memory_utilization', 0)
        
        options = []
        
        # Düşük kullanım oranı varsa daha küçük bir VM öner
        if cpu_utilization < 20 and memory_utilization < 30:
            options.append(f"Daha küçük bir VM boyutuna geçin (%50'ye kadar tasarruf, kullanım: CPU {cpu_utilization}%, Bellek {memory_utilization}%)")
        
        # Reserved Instance değerlendirmesi
        options.append("1 veya 3 yıllık Reserved Instance satın alın (%40-70 tasarruf)")
        
        # Spot/Low-priority VM değerlendirmesi
        options.append("Toleranslı workload'lar için Spot VM'leri değerlendirin (%80'e kadar tasarruf)")
        
        # Özel VM serilerini değerlendirme
        if 'standard_d' in size.lower():
            options.append("B-serisi burstable VM'lere geçmeyi değerlendirin (düşük ortalama CPU kullanımı için)")
        elif 'standard_e' in size.lower():
            options.append("D-serisi VM'lere geçmeyi değerlendirin (yüksek bellek gereksiniminiz yoksa)")
        
        return {
            'resource_id': resource['id'],
            'resource_name': resource['name'],
            'resource_type': resource['type'],
            'resource_group': resource['resource_group'],
            'issue': f"Bu VM yüksek maliyetlidir: {monthly_cost:.2f} USD/ay",
            'cost_impact': monthly_cost,
            'recommendations': options,
            'potential_savings': {
                'monthly_ri_savings': monthly_cost * 0.4,  # RI ile %40 tasarruf
                'yearly_ri_savings': monthly_cost * 0.4 * 12,
                'sizing_savings': monthly_cost * 0.3 if cpu_utilization < 20 else 0  # Doğru boyutlandırma ile %30 tasarruf
            },
            'resource_details': {
                'size': size,
                'cpu_utilization': f"{cpu_utilization}%",
                'memory_utilization': f"{memory_utilization}%"
            },
            'estimated_effort': 'Orta',
            'risk_level': 'Orta',
            'recommendation_type': 'VM Maliyet Optimizasyonu'
        }
    
    def _analyze_high_cost_storage(self, resource, monthly_cost):
        """
        Yüksek maliyetli storage hesapları için detaylı analiz ve maliyet düşürme önerileri.
        """
        tier = resource.get('tier', 'bilinmiyor')
        replication = resource.get('replication', 'bilinmiyor')
        
        options = []
        
        # Erişim Katmanı Önerileri
        options.append("Blob'lar için erişim sıklığına göre katmanlı depolama (Hot/Cool/Archive) kullanın")
        
        # Yaşam Döngüsü Yönetimi
        options.append("Eski verileri otomatik olarak daha ucuz katmanlara taşımak için yaşam döngüsü politikaları uygulayın")
        
        # Yedekleme Stratejisi
        if replication.lower() in ['grs', 'ra-grs']:
            options.append(f"Kritik olmayan veriler için LRS depolamaya geçin ({replication} yerine)")
        
        # Kullanılmayan verileri temizleme
        options.append("Eski, gereksiz verileri temizleyin veya arşivleyin")
        
        return {
            'resource_id': resource['id'],
            'resource_name': resource['name'],
            'resource_type': resource['type'],
            'resource_group': resource['resource_group'],
            'issue': f"Bu depolama hesabı yüksek maliyetlidir: {monthly_cost:.2f} USD/ay",
            'cost_impact': monthly_cost,
            'recommendations': options,
            'potential_savings': {
                'monthly_lifecycle_savings': monthly_cost * 0.3,  # Yaşam döngüsü ile %30 tasarruf
                'replication_change_savings': monthly_cost * 0.4 if replication.lower() in ['grs', 'ra-grs'] else 0  # Replikasyon düşürme ile %40 tasarruf
            },
            'resource_details': {
                'tier': tier,
                'replication': replication,
                'total_size': resource.get('total_size', 'bilinmiyor')
            },
            'estimated_effort': 'Orta',
            'risk_level': 'Düşük',
            'recommendation_type': 'Storage Maliyet Optimizasyonu'
        }
        
    # Diğer yüksek maliyetli kaynak türleri için analiz fonksiyonları benzer şekilde eklenebilir
    def _analyze_high_cost_sql(self, resource, monthly_cost):
        # SQL DB özgü maliyet analizi...
        pass
        
    def _analyze_high_cost_cosmos(self, resource, monthly_cost):
        # CosmosDB özgü maliyet analizi...
        pass
        
    def _analyze_high_cost_aks(self, resource, monthly_cost):
        # AKS özgü maliyet analizi...
        pass
        
    def _analyze_high_cost_app_service_plan(self, resource, monthly_cost):
        # App Service Plan özgü maliyet analizi...
        pass 