"""
Sanal makineler için analiz modülü.
"""

import logging
from modules.analyzers.resource_analyzer import ResourceAnalyzer

logger = logging.getLogger("VMAnalyzer")

class VMAnalyzer(ResourceAnalyzer):
    """
    Sanal makineleri analiz eden sınıf.
    """
    
    def __init__(self, azure_client, config):
        """
        VM analizörünü başlatır.
        
        Args:
            azure_client: Azure istemcisi
            config: Uygulama yapılandırması
        """
        super().__init__(azure_client, config)
        self.resource_type_name = "Virtual Machine"
    
    def analyze(self):
        """
        Sanal makineleri analiz eder.
        
        Returns:
            İnaktif sanal makinelerin listesi
        """
        logger.info("Sanal makineler analiz ediliyor...")
        inactive_vms = []
        
        try:
            # Tüm sanal makineleri listele
            vms = list(self.azure_client.compute_client.virtual_machines.list_all())
            
            for vm in vms:
                resource_group = self.azure_client.extract_resource_group(vm.id)
                
                # VM'in durumunu kontrol et
                instance_view = self.azure_client.compute_client.virtual_machines.instance_view(
                    resource_group, vm.name)
                power_state = next((status.code for status in instance_view.statuses 
                                   if status.code.startswith('PowerState/')), None)
                
                # VM'in CPU kullanımını al
                cpu_usage = self.azure_client.get_resource_metric(
                    vm.id,
                    'Percentage CPU',
                    self.config.start_time,
                    self.config.end_time
                )
                
                # İnaktif mi kontrol et
                is_inactive = False
                inactive_reason = ""
                
                if power_state == 'PowerState/deallocated':
                    is_inactive = True
                    inactive_reason = "VM deallocated durumunda"
                elif not cpu_usage or self.is_metric_inactive(cpu_usage, self.config.metric_thresholds['vm_cpu_threshold']):
                    is_inactive = True
                    inactive_reason = "Düşük CPU kullanımı"
                
                if is_inactive:
                    vm_size = vm.hardware_profile.vm_size
                    vm_state = power_state.replace('PowerState/', '') if power_state else 'Unknown'
                    
                    inactive_vms.append(self.create_resource_entry(
                        vm, vm_state, inactive_reason, vm_size
                    ))
            
            logger.info(f"{len(inactive_vms)} inaktif sanal makine bulundu.")
            return inactive_vms
            
        except Exception as e:
            logger.error(f"Sanal makineler analiz edilirken hata oluştu: {str(e)}")
            return [] 