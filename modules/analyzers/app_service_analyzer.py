"""
App Service uygulamaları için analiz modülü.
"""

import logging
from modules.analyzers.resource_analyzer import ResourceAnalyzer

logger = logging.getLogger("AppServiceAnalyzer")

class AppServiceAnalyzer(ResourceAnalyzer):
    """
    App Service uygulamalarını analiz eden sınıf.
    """
    
    def __init__(self, azure_client, config):
        """
        App Service analizörünü başlatır.
        
        Args:
            azure_client: Azure istemcisi
            config: Uygulama yapılandırması
        """
        super().__init__(azure_client, config)
        self.resource_type_name = "App Service"
    
    def analyze(self):
        """
        App Service uygulamalarını analiz eder.
        
        Returns:
            İnaktif App Service uygulamalarının listesi
        """
        logger.info("App Service uygulamaları analiz ediliyor...")
        inactive_apps = []
        
        try:
            # Tüm web uygulamalarını listele
            web_apps = list(self.azure_client.web_client.web_apps.list())
            
            for app in web_apps:
                # HTTP istek metriklerini al
                http_requests = self.azure_client.get_resource_metric(
                    app.id,
                    'Requests',
                    self.config.start_time,
                    self.config.end_time,
                    aggregation="Total"  # Toplam istek sayısı
                )
                
                # İnaktif mi kontrol et
                is_inactive = False
                inactive_reason = ""
                
                if not http_requests or self.is_metric_inactive(
                    http_requests, self.config.metric_thresholds['app_service_requests_threshold']):
                    is_inactive = True
                    inactive_reason = "Düşük HTTP istek sayısı"
                
                if is_inactive:
                    # SKU bilgisini al
                    sku = "Unknown"
                    try:
                        # App Service planını bulmaya çalış
                        if hasattr(app, 'server_farm_id') and app.server_farm_id:
                            resource_group = self.azure_client.extract_resource_group(app.server_farm_id)
                            plan_name = app.server_farm_id.split('/')[-1]
                            app_plan = self.azure_client.web_client.app_service_plans.get(
                                resource_group, plan_name)
                            sku = app_plan.sku.name if hasattr(app_plan, 'sku') and app_plan.sku else "Unknown"
                    except Exception:
                        pass
                    
                    inactive_apps.append(self.create_resource_entry(
                        app, app.state, inactive_reason, sku
                    ))
            
            logger.info(f"{len(inactive_apps)} inaktif App Service uygulaması bulundu.")
            return inactive_apps
            
        except Exception as e:
            logger.error(f"App Service uygulamaları analiz edilirken hata oluştu: {str(e)}")
            return [] 