"""
Azure Cost Optimizer - Çoklu Hesap Desteği ile Ana modül
Birden fazla Azure hesabınızın kaynaklarını analiz ederek maliyet tasarrufu sağlayan öneriler sunar.
"""

import os
import argparse
import logging
from datetime import datetime
from typing import List, Dict, Any

# Modüller
from modules.azure_client import AzureClientManager, AzureClient
from modules.analyzers.resource_analyzer import ResourceAnalyzer
from modules.analyzers.vm_analyzer import VMAnalyzer
from modules.analyzers.app_service_analyzer import AppServiceAnalyzer
from modules.analyzers.storage_analyzer import StorageAnalyzer
from modules.analyzers.sql_analyzer import SQLAnalyzer
from modules.analyzers.cosmos_analyzer import CosmosDBAnalyzer
from modules.analyzers.aks_analyzer import AKSAnalyzer
from modules.cost_analyzer import CostAnalyzer
from modules.optimizer import OptimizationRecommender
from modules.reporter import ReportGenerator
from modules.config import AppConfig, AccountConfig

# Logging yapılandırması
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("AzureCostOptimizer")

class AzureCostOptimizer:
    """
    Birden fazla Azure hesabını analiz ederek maliyet optimizasyonu önerileri sunan ana sınıf.
    """
    
    def __init__(self, subscription_ids=None, config=None):
        """
        Azure Cost Optimizer'ı başlatır.
        
        Args:
            subscription_ids: Azure Abonelik ID'leri listesi (None ise tüm abonelikler taranır)
            config: Uygulama yapılandırması (None ise varsayılan yapılandırma kullanılır)
        """
        self.config = config or AppConfig()
        
        # Çıktı dizinini oluştur
        os.makedirs(self.config.output_dir, exist_ok=True)
        
        # Azure istemci yöneticisini başlat
        self.client_manager = AzureClientManager()
        
        # Abonelikleri belirle
        self.subscription_ids = subscription_ids or []
        if not self.subscription_ids:
            # Kullanıcının erişimi olan tüm abonelikleri al
            try:
                subscriptions = self.client_manager.list_subscriptions()
                self.subscription_ids = [sub.subscription_id for sub in subscriptions]
                logger.info(f"{len(self.subscription_ids)} abonelik bulundu")
            except Exception as e:
                logger.error(f"Abonelikler listelenirken hata: {str(e)}")
                self.subscription_ids = []
        
        # Her abonelik için konfigürasyon oluştur
        for sub_id in self.subscription_ids:
            # Eğer bu abonelik için konfigürasyon yoksa ekle
            exists = any(acc.subscription_id == sub_id for acc in self.config.accounts)
            if not exists:
                self.config.accounts.append(AccountConfig(sub_id))
        
        # Analiz sonuçları - abonelik ID'sine göre organize edilmiş
        self.inactive_resources = {}  # {subscription_id: [resources]}
        self.high_cost_resources = {}  # {subscription_id: [resources]}
        self.recommendations = {}  # {subscription_id: [recommendations]}
        
        logger.info(f"Azure Cost Optimizer başlatıldı - {len(self.subscription_ids)} abonelik")
    
    def analyze_resources(self):
        """
        Tüm aboneliklerdeki kaynakları analiz eder.
        """
        logger.info(f"Kaynaklar analiz ediliyor - {len(self.subscription_ids)} abonelik")
        
        for sub_id in self.subscription_ids:
            try:
                # Abonelik için yapılandırmayı bul
                account_config = next((acc for acc in self.config.accounts if acc.subscription_id == sub_id), None)
                if not account_config:
                    logger.warning(f"Abonelik için yapılandırma bulunamadı: {sub_id}, atlanıyor.")
                    continue
                
                # Abonelik için Azure istemcisini al
                azure_client = self.client_manager.get_client(sub_id)
                
                # Her analizörü oluştur ve çalıştır
                vm_analyzer = VMAnalyzer(azure_client, account_config)
                app_service_analyzer = AppServiceAnalyzer(azure_client, account_config)
                storage_analyzer = StorageAnalyzer(azure_client, account_config)
                sql_analyzer = SQLAnalyzer(azure_client, account_config)
                cosmos_analyzer = CosmosDBAnalyzer(azure_client, account_config)
                aks_analyzer = AKSAnalyzer(azure_client, account_config)
                
                # İnaktif kaynakları belirle
                inactive_vms = vm_analyzer.analyze()
                inactive_apps = app_service_analyzer.analyze()
                inactive_storages = storage_analyzer.analyze()
                inactive_dbs = sql_analyzer.analyze()
                inactive_cosmos = cosmos_analyzer.analyze()
                inactive_aks = aks_analyzer.analyze()
                
                # İnaktif kaynakları birleştir
                subscription_inactive = []
                subscription_inactive.extend(inactive_vms)
                subscription_inactive.extend(inactive_apps)
                subscription_inactive.extend(inactive_storages)
                subscription_inactive.extend(inactive_dbs)
                subscription_inactive.extend(inactive_cosmos)
                subscription_inactive.extend(inactive_aks)
                
                # Maliyet analizörünü oluştur
                cost_analyzer = CostAnalyzer(azure_client, account_config)
                
                # Kaynaklara maliyet verilerini ekle
                cost_analyzer.add_costs_to_resources(subscription_inactive)
                
                # Yüksek maliyetli kaynakları belirle
                subscription_high_cost = cost_analyzer.get_high_cost_resources()
                
                # Optimizasyon önerilerini oluştur
                optimizer = OptimizationRecommender(azure_client)
                subscription_recommendations = optimizer.generate_recommendations(
                    subscription_inactive, subscription_high_cost)
                
                # Sonuçları depolama yapısına ekle
                self.inactive_resources[sub_id] = subscription_inactive
                self.high_cost_resources[sub_id] = subscription_high_cost
                self.recommendations[sub_id] = subscription_recommendations
                
                logger.info(f"Abonelik analizi tamamlandı: {sub_id}")
                logger.info(f"  İnaktif kaynaklar: {len(subscription_inactive)}")
                logger.info(f"  Yüksek maliyetli kaynaklar: {len(subscription_high_cost)}")
                logger.info(f"  Optimizasyon önerileri: {len(subscription_recommendations)}")
                
            except Exception as e:
                logger.error(f"Abonelik analiz edilirken hata: {sub_id} - {str(e)}")
        
        total_inactive = sum(len(resources) for resources in self.inactive_resources.values())
        total_high_cost = sum(len(resources) for resources in self.high_cost_resources.values())
        total_recommendations = sum(len(recs) for recs in self.recommendations.values())
        
        logger.info(f"Tüm abonelikler için analiz tamamlandı.")
        logger.info(f"Toplam inaktif kaynaklar: {total_inactive}")
        logger.info(f"Toplam yüksek maliyetli kaynaklar: {total_high_cost}")
        logger.info(f"Toplam optimizasyon önerileri: {total_recommendations}")
    
    def generate_reports(self):
        """
        Tüm abonelikler için raporları oluşturur.
        """
        logger.info("Raporlar oluşturuluyor...")
        
        # Rapor oluşturucuyu başlat
        reporter = ReportGenerator(self.config.output_dir)
        
        # Hesap yapılandırmalarını sözlük formatına dönüştür
        account_configs = {acc.subscription_id: {
            'display_name': acc.display_name,
            'days_inactive': acc.days_inactive,
            'cost_threshold': acc.cost_threshold
        } for acc in self.config.accounts}
        
        # Raporları oluştur
        reporter.generate_inactive_resource_report(self.inactive_resources)
        reporter.generate_high_cost_report(self.high_cost_resources)
        reporter.generate_recommendations_report(self.recommendations)
        reporter.generate_charts(self.inactive_resources)
        reporter.generate_summary_report(
            self.inactive_resources, 
            self.high_cost_resources, 
            self.recommendations,
            account_configs
        )
        reporter.generate_visualization(self.inactive_resources)
        
        logger.info("Raporlar başarıyla oluşturuldu.")
    
    def deactivate_resources(self, dry_run=True):
        """
        İnaktif kaynakları devre dışı bırakır.
        
        Args:
            dry_run: Eğer True ise, devre dışı bırakma işlemini simüle eder (gerçek değişiklik yapmaz)
        """
        for sub_id, resources in self.inactive_resources.items():
            if not resources:
                continue
                
            logger.info(f"Abonelik için inaktif kaynaklar devre dışı bırakılıyor: {sub_id}")
            logger.info(f"Toplam {len(resources)} kaynak, {'SİMÜLASYON MODU' if dry_run else 'GERÇEK MOD'}")
            
            try:
                azure_client = self.client_manager.get_client(sub_id)
                
                for resource in resources:
                    resource_id = resource['id']
                    resource_name = resource['name']
                    resource_type = resource['type'].lower()
                    
                    logger.info(f"Kaynak devre dışı bırakılıyor: {resource_name} ({resource_type})")
                    
                    if dry_run:
                        logger.info(f"[SİMÜLASYON] Kaynak devre dışı bırakılacaktı: {resource_name}")
                        continue
                    
                    try:
                        # Kaynak türüne göre devre dışı bırakma işlemi
                        if 'microsoft.compute/virtualmachines' in resource_type:
                            # VM'i deallocate et
                            resource_group = azure_client.extract_resource_group(resource_id)
                            azure_client.compute_client.virtual_machines.deallocate(
                                resource_group, resource_name)
                            
                            logger.info(f"VM başarıyla devre dışı bırakıldı: {resource_name}")
                        
                        elif 'microsoft.web/sites' in resource_type:
                            # App Service'i durdur
                            resource_group = azure_client.extract_resource_group(resource_id)
                            azure_client.web_client.web_apps.stop(resource_group, resource_name)
                            
                            logger.info(f"App Service başarıyla durduruldu: {resource_name}")
                        
                        # Diğer kaynak türleri için benzer işlemler eklenebilir
                        else:
                            logger.warning(f"Bu kaynak türü için devre dışı bırakma işlemi desteklenmiyor: {resource_type}")
                        
                    except Exception as e:
                        logger.error(f"Kaynak devre dışı bırakılırken hata: {resource_name} - {str(e)}")
                
            except Exception as e:
                logger.error(f"Abonelik kaynakları devre dışı bırakılırken hata: {sub_id} - {str(e)}")

def main():
    """
    Ana işlev.
    """
    parser = argparse.ArgumentParser(description='Azure Cost Optimizer - Çoklu hesap desteği ile')
    parser.add_argument('--subscriptions', type=str, nargs='*', 
                      help='Analiz edilecek Azure Abonelik ID\'leri (boş ise tüm abonelikler)')
    parser.add_argument('--days', type=int, default=30,
                      help='Bir kaynağın inaktif sayılması için gün sayısı (varsayılan: 30)')
    parser.add_argument('--cost-threshold', type=float, default=10.0,
                      help='Yüksek maliyet eşiği (USD, varsayılan: 10.0)')
    parser.add_argument('--output-dir', type=str, default='reports',
                      help='Raporların kaydedileceği dizin (varsayılan: reports)')
    parser.add_argument('--deactivate', action='store_true',
                      help='İnaktif kaynakları devre dışı bırak')
    parser.add_argument('--dry-run', action='store_true',
                      help='Simülasyon modu (gerçek değişiklik yapmaz)')
    
    args = parser.parse_args()
    
    # Yapılandırmayı oluştur
    config = AppConfig(output_dir=args.output_dir)
    
    try:
        # Belirtilen abonelikler varsa bunları kullan, yoksa tüm abonelikleri kullan
        subscription_ids = args.subscriptions if args.subscriptions else None
        
        # Her abonelik için yapılandırmayı ekle (eğer subscription_ids belirtilmişse)
        if subscription_ids:
            for sub_id in subscription_ids:
                config.accounts.append(AccountConfig(
                    subscription_id=sub_id,
                    days_inactive=args.days,
                    cost_threshold=args.cost_threshold
                ))
        
        # Optimizer'ı başlat
        optimizer = AzureCostOptimizer(subscription_ids, config)
        
        # Kaynakları analiz et
        optimizer.analyze_resources()
        
        # Raporları oluştur
        optimizer.generate_reports()
        
        # İnaktif kaynakları devre dışı bırak (istenirse)
        if args.deactivate:
            optimizer.deactivate_resources(dry_run=args.dry_run)
            
        logger.info("İşlem başarıyla tamamlandı.")
    except Exception as e:
        logger.error(f"İşlem sırasında hata oluştu: {str(e)}")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())
