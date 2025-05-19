"""
Azure servislerine bağlanmak için istemci modülü.
"""

import logging
from azure.identity import DefaultAzureCredential, InteractiveBrowserCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.monitor import MonitorManagementClient
from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.web import WebSiteManagementClient
from azure.mgmt.cosmosdb import CosmosDBManagementClient
from azure.mgmt.consumption import ConsumptionManagementClient
from azure.mgmt.sql import SqlManagementClient
from azure.mgmt.containerservice import ContainerServiceClient
from azure.mgmt.reservations import AzureReservationAPI

logger = logging.getLogger("AzureClient")

class AzureClientManager:
    """
    Birden fazla Azure hesabı için istemci yöneticisi.
    """
    
    def __init__(self, credential=None):
        """
        Yönetici sınıfını başlatır.
        
        Args:
            credential: Önceden oluşturulmuş Azure kimlik bilgisi (None ise otomatik oluşturulur)
        """
        self._clients = {}  # subscription_id -> AzureClient
        self.credential = credential or self._get_credentials()
    
    def _get_credentials(self):
        """
        Azure kimlik bilgilerini döndürür.
        """
        try:
            # Önce DefaultAzureCredential kullan (environment vars, managed identity, vs.)
            credential = DefaultAzureCredential()
            return credential
        except Exception as e:
            logger.warning(f"DefaultAzureCredential başarısız oldu: {str(e)}")
            
            # Tarayıcı tabanlı etkileşimli oturum aç
            try:
                credential = InteractiveBrowserCredential()
                return credential
            except Exception as e:
                logger.error(f"InteractiveBrowserCredential başarısız oldu: {str(e)}")
                raise Exception("Azure kimlik doğrulaması başarısız oldu.")
    
    def get_client(self, subscription_id):
        """
        Belirtilen abonelik için AzureClient döndürür, yoksa oluşturur.
        
        Args:
            subscription_id: Azure Abonelik ID'si
            
        Returns:
            AzureClient nesnesi
        """
        if subscription_id not in self._clients:
            self._clients[subscription_id] = AzureClient(subscription_id, self.credential)
        
        return self._clients[subscription_id]
    
    def list_subscriptions(self):
        """
        Kullanıcının erişimine sahip abonelikleri listeler.
        
        Returns:
            Abonelik nesnelerinin listesi
        """
        try:
            # Önce azure-mgmt-subscription ile deneyin
            try:
                from azure.mgmt.subscription import SubscriptionClient
                subscription_client = SubscriptionClient(self.credential)
                return list(subscription_client.subscriptions.list())
            except ImportError:
                # Azure mgmt subscription paketi yüklü değilse alternatif yöntemi kullan
                logger.info("azure-mgmt-subscription paketi bulunamadı, alternatif yöntem kullanılıyor")
                from modules.subscription_client import SubscriptionClient
                subscription_client = SubscriptionClient(self.credential)
                return subscription_client.subscriptions.list()
        except Exception as e:
            logger.error(f"Abonelikler listelenirken hata: {str(e)}")
            return []

class AzureClient:
    """
    Azure servislerine bağlanmak için kullanılan istemci sınıfı.
    """
    
    def __init__(self, subscription_id, credential=None):
        """
        Azure istemcilerini başlatır.
        
        Args:
            subscription_id: Azure Abonelik ID'si
            credential: Azure kimlik bilgisi nesnesi (None ise otomatik oluşturulur)
        """
        self.subscription_id = subscription_id
        self.credential = credential or self._get_credentials()
        
        # Azure servisleri için istemcileri oluştur
        self.resource_client = ResourceManagementClient(self.credential, subscription_id)
        self.compute_client = ComputeManagementClient(self.credential, subscription_id)
        self.monitor_client = MonitorManagementClient(self.credential, subscription_id)
        self.storage_client = StorageManagementClient(self.credential, subscription_id)
        self.web_client = WebSiteManagementClient(self.credential, subscription_id)
        self.cosmosdb_client = CosmosDBManagementClient(self.credential, subscription_id)
        self.consumption_client = ConsumptionManagementClient(self.credential, subscription_id)
        self.sql_client = SqlManagementClient(self.credential, subscription_id)
        self.aks_client = ContainerServiceClient(self.credential, subscription_id)
        self.reservation_client = AzureReservationAPI(self.credential)
        
        logger.info(f"Azure istemcileri başarıyla başlatıldı - Abonelik: {subscription_id}")
    
    def _get_credentials(self):
        """
        Azure kimlik bilgilerini döndürür.
        
        Returns:
            Azure kimlik doğrulama nesnesi
        """
        try:
            # Önce DefaultAzureCredential'ı dene
            credential = DefaultAzureCredential()
            # Test et
            ResourceManagementClient(credential, self.subscription_id)
            logger.info("Varsayılan Azure kimlik doğrulama başarılı.")
            return credential
        except Exception as e:
            logger.info(f"Varsayılan kimlik doğrulama başarısız: {str(e)}")
            logger.info("Tarayıcı üzerinden kimlik doğrulama deneniyor...")
            credential = InteractiveBrowserCredential()
            return credential
    
    def get_resource_metric(self, resource_id, metric_name, start_time, end_time, aggregation="Average"):
        """
        Belirli bir kaynağın metrik verilerini alır.
        
        Args:
            resource_id: Azure kaynak ID'si
            metric_name: Metrik adı
            start_time: Başlangıç zamanı
            end_time: Bitiş zamanı
            aggregation: Toplama yöntemi (Average, Total, Maximum, Minimum)
            
        Returns:
            Ortalama metrik değeri veya None (metrik yoksa)
        """
        try:
            metrics_data = self.monitor_client.metrics.list(
                resource_id,
                timespan=f"{start_time.isoformat()}/{end_time.isoformat()}",
                interval='P1D',
                metricnames=metric_name,
                aggregation=aggregation
            )
            
            # Metrikleri topla
            if metrics_data.value and metrics_data.value[0].timeseries:
                values = []
                for point in metrics_data.value[0].timeseries[0].data:
                    # Toplama yöntemine göre değeri al
                    if aggregation == 'Average' and point.average is not None:
                        values.append(point.average)
                    elif aggregation == 'Total' and point.total is not None:
                        values.append(point.total)
                    elif aggregation == 'Maximum' and point.maximum is not None:
                        values.append(point.maximum)
                    elif aggregation == 'Minimum' and point.minimum is not None:
                        values.append(point.minimum)
                
                # Değerlerin ortalamasını al
                if values:
                    return sum(values) / len(values)
            
            return None
        except Exception as e:
            logger.warning(f"Metrik verisi alınamadı - {resource_id}, {metric_name}: {str(e)}")
            return None
    
    def extract_resource_group(self, resource_id):
        """
        Kaynak ID'sinden resource group adını çıkarır.
        
        Args:
            resource_id: Azure kaynak ID'si
            
        Returns:
            Resource group adı
        """
        parts = resource_id.split('/')
        for i, part in enumerate(parts):
            if part.lower() == 'resourcegroups' and i + 1 < len(parts):
                return parts[i + 1]
        return None 