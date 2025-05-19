"""
Azure aboneliklerini yönetmek için alternatif modül.
azure-mgmt-subscription paketi olmadan çalışır.
"""

import logging
from azure.identity import DefaultAzureCredential

logger = logging.getLogger(__name__)

class SubscriptionClient:
    """
    Azure aboneliklerini listeleyen basit istemci.
    """
    
    def __init__(self, credential=None):
        """
        İstemciyi başlatır.
        
        Args:
            credential: Azure kimlik bilgisi
        """
        self.credential = credential or DefaultAzureCredential()
        self.subscriptions = SubscriptionOperations(self.credential)

class SubscriptionOperations:
    """
    Abonelik işlemleri.
    """
    
    def __init__(self, credential):
        """
        İşlemleri başlatır.
        
        Args:
            credential: Azure kimlik bilgisi
        """
        self.credential = credential
    
    def list(self):
        """
        Kullanılabilir abonelikleri listeler.
        
        Returns:
            Subscription nesnelerinin listesi
        """
        # Azure Management REST API kullanarak abonelikleri al
        from azure.core.pipeline import PipelineClient
        from azure.core.pipeline.policies import BearerTokenCredentialPolicy
        from azure.core.pipeline.policies import RetryPolicy, NetworkTraceLoggingPolicy
        
        base_url = "https://management.azure.com"
        scope = "https://management.azure.com/.default"
        
        # İstemciyi yapılandır
        policies = [
            BearerTokenCredentialPolicy(self.credential, scope),
            RetryPolicy(),
            NetworkTraceLoggingPolicy()
        ]
        
        client = PipelineClient(base_url=base_url, policies=policies)
        
        # Abonelikleri getir
        request = client.get("/subscriptions?api-version=2020-01-01")
        response = client.send_request(request)
        
        if response.status_code == 200:
            data = response.json()
            return [Subscription(sub) for sub in data.get('value', [])]
        else:
            logger.error(f"Abonelikler alınamadı: {response.status_code} - {response.reason}")
            return []

class Subscription:
    """
    Azure aboneliği.
    """
    
    def __init__(self, sub_data):
        """
        Aboneliği başlatır.
        
        Args:
            sub_data: Abonelik JSON verisi
        """
        self.id = sub_data.get('id')
        self.subscription_id = sub_data.get('subscriptionId')
        self.display_name = sub_data.get('displayName')
        self.state = sub_data.get('state') 