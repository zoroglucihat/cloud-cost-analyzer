"""
Azure Cost Optimizer için çeviri modülü.
"""

class Translator:
    """
    Metin çevirisi için sınıf.
    """
    
    LANGUAGES = {
        'en': 'English',
        'tr': 'Türkçe'
    }
    
    def __init__(self, language='en'):
        """
        Çeviriciyi başlatır.
        
        Args:
            language: Kullanılacak dil kodu (varsayılan: 'en')
        """
        self.language = language
        
        # Çeviriler sözlüğü
        self.translations = {
            # English translations
            'en': {
                'app_subtitle': 'Analyze and optimize your Azure resources across multiple subscriptions',
                'connecting_azure': 'Connecting to Azure...',
                'connected_azure': 'Connected to Azure. Found {} subscriptions.',
                'connection_error': 'Error connecting to Azure: {}',
                'settings': 'Settings',
                'subscription_selection': 'Subscription Selection',
                'select_subscriptions': 'Select Subscriptions to Analyze',
                'no_subscription_selected': 'No subscription selected. Please select at least one subscription.',
                'analysis_parameters': 'Analysis Parameters',
                'days_inactive': 'Days Inactive',
                'days_inactive_help': 'Number of days a resource must be inactive to be included in the report',
                'cost_threshold': 'Cost Threshold (USD)',
                'cost_threshold_help': 'Minimum monthly cost for a resource to be considered high-cost',
                'output_dir': 'Output Directory',
                'output_dir_help': 'Directory where reports will be saved',
                'actions': 'Actions',
                'analyze_button': 'Analyze Resources',
                'deactivate_button': 'Deactivate Inactive Resources',
                'deactivate_help': 'Deallocate VMs and stop App Services for inactive resources',
                'dry_run': 'Simulation Mode (No Changes)',
                'dry_run_help': 'Only simulate deactivation without making actual changes',
                'analyzing': 'Analyzing...',
                'analyzing_resources': 'Analyzing resources...',
                'generating_reports': 'Generating reports...',
                'analysis_complete': 'Analysis complete!',
                'analysis_success': 'Analysis completed successfully!',
                'deactivating_resources': 'Deactivating resources...',
                'deactivation_simulation_success': 'Simulation of resource deactivation completed successfully',
                'deactivation_success': 'Resources have been deactivated successfully',
                'error_analysis': 'Error during analysis: {}',
                'error_deactivation': 'Error deactivating resources: {}',
                'tab_inactive': 'Inactive Resources',
                'tab_high_cost': 'High Cost Resources',
                'tab_recommendations': 'Recommendations',
                'tab_report': 'Summary Report',
                'inactive_resources': 'Inactive Resources',
                'select_sub_to_view': 'Select Subscription to View',
                'all_subscriptions': 'All Subscriptions',
                'col_subscription': 'Subscription',
                'col_name': 'Name',
                'col_type': 'Type',
                'col_resource_group': 'Resource Group',
                'col_location': 'Location',
                'col_size': 'Size',
                'col_state': 'State',
                'col_reason': 'Reason',
                'col_cost': 'Cost (USD/month)',
                'download_csv': 'Download CSV',
                'no_inactive_resources': 'No inactive resources found',
                'no_inactive_resources_for_sub': 'No inactive resources found for this subscription',
                'high_cost_resources': 'High Cost Resources',
                'optimization_recommendations': 'Optimization Recommendations',
                'summary_report': 'Summary Report',
                'download_html': 'Download HTML Report',
                'no_report': 'No summary report found. Please run analysis first.',
                'subscription_management': 'Subscription Management',
                'enter_subscription_id': 'Enter Subscription ID',
                'enter_subscription_name': 'Enter Display Name (optional)',
                'add_subscription': 'Add',
                'current_subscriptions': 'Current Subscriptions',
                'no_subscriptions_added': 'No subscriptions added yet. Add at least one subscription ID above.',
                'remove': 'Remove',
                'analyzing_subscription': 'Analyzing subscription',
                'error_analyzing_subscription': 'Error analyzing subscription',
                'deactivating_resources_for': 'Deactivating resources for subscription',
                'azure_authentication': 'Azure Authentication',
                'auth_method': 'Authentication Method',
                'auth_method_service_principal': 'Service Principal',
                'auth_method_interactive': 'Interactive Browser',
                'auth_method_default': 'Default Credentials',
                'auth_method_manual': 'Manual (Skip Authentication)',
                'service_principal_auth': 'Service Principal Authentication',
                'tenant_id': 'Tenant ID',
                'client_id': 'Client ID (App ID)',
                'client_secret': 'Client Secret',
                'connect': 'Connect to Azure',
                'login_interactive': 'Login with Browser',
                'login_default': 'Login with Default Credentials',
                'skip_auth': 'Skip Authentication',
                'manual_mode_enabled': 'Manual mode enabled. You can now add subscription IDs manually.',
                'auth_error': 'Authentication error: {}',
                'connected_azure_sp': 'Connected to Azure using Service Principal',
                'connected_azure_interactive': 'Connected to Azure using Interactive Browser Authentication',
                'connected_azure_default': 'Connected to Azure using Default Credentials',
                'interactive_auth_info': 'A browser window will open. Please log in with your Azure account.',
                'default_auth_info': 'Uses environment variables, managed identity, or Visual Studio/VSCode credentials.',
                'manual_auth_warning': 'You will need to manually enter subscription IDs. Limited functionality may be available.',
                'change_auth': 'Change Authentication',
                'auth_status_service_principal': 'Connected with Service Principal',
                'auth_status_interactive': 'Connected with Interactive Browser Authentication',
                'auth_status_default': 'Connected with Default Credentials',
                'auth_status_manual': 'Manual Mode (No Azure Authentication)',
                'list_subscriptions': 'Load Available Subscriptions',
                'loading_subscriptions': 'Loading subscriptions...',
                'subscriptions_loaded': 'Loaded {} subscriptions',
                'deactivate_options': 'Deactivation Options',
                'subscription_list_error': 'Error listing subscriptions: {}',
            },
            
            # Turkish translations
            'tr': {
                'app_subtitle': 'Birden fazla abonelik için Azure kaynaklarınızı analiz edin ve optimize edin',
                'connecting_azure': 'Azure\'a bağlanıyor...',
                'connected_azure': 'Azure\'a bağlandı. {} abonelik bulundu.',
                'connection_error': 'Azure\'a bağlanırken hata: {}',
                'settings': 'Ayarlar',
                'subscription_selection': 'Abonelik Seçimi',
                'select_subscriptions': 'Analiz Edilecek Abonelikleri Seçin',
                'no_subscription_selected': 'Abonelik seçilmedi. Lütfen en az bir abonelik seçin.',
                'analysis_parameters': 'Analiz Parametreleri',
                'days_inactive': 'İnaktif Gün Sayısı',
                'days_inactive_help': 'Bir kaynağın inaktif sayılması için geçmesi gereken gün sayısı',
                'cost_threshold': 'Maliyet Eşiği (USD)',
                'cost_threshold_help': 'Bir kaynağın yüksek maliyetli sayılması için aylık minimum maliyet',
                'output_dir': 'Çıktı Dizini',
                'output_dir_help': 'Raporların kaydedileceği dizin',
                'actions': 'İşlemler',
                'analyze_button': 'Kaynakları Analiz Et',
                'deactivate_button': 'İnaktif Kaynakları Devre Dışı Bırak',
                'deactivate_help': 'İnaktif sanal makineleri deallocate et ve App Service\'leri durdur',
                'dry_run': 'Simülasyon Modu (Değişiklik Yok)',
                'dry_run_help': 'Gerçek değişiklik yapmadan yalnızca devre dışı bırakma simülasyonu yap',
                'analyzing': 'Analiz ediliyor...',
                'analyzing_resources': 'Kaynaklar analiz ediliyor...',
                'generating_reports': 'Raporlar oluşturuluyor...',
                'analysis_complete': 'Analiz tamamlandı!',
                'analysis_success': 'Analiz başarıyla tamamlandı!',
                'deactivating_resources': 'Kaynaklar devre dışı bırakılıyor...',
                'deactivation_simulation_success': 'Kaynak devre dışı bırakma simülasyonu başarıyla tamamlandı',
                'deactivation_success': 'Kaynaklar başarıyla devre dışı bırakıldı',
                'error_analysis': 'Analiz sırasında hata: {}',
                'error_deactivation': 'Kaynakları devre dışı bırakırken hata: {}',
                'tab_inactive': 'İnaktif Kaynaklar',
                'tab_high_cost': 'Yüksek Maliyetli Kaynaklar',
                'tab_recommendations': 'Öneriler',
                'tab_report': 'Özet Rapor',
                'inactive_resources': 'İnaktif Kaynaklar',
                'select_sub_to_view': 'Görüntülenecek Aboneliği Seçin',
                'all_subscriptions': 'Tüm Abonelikler',
                'col_subscription': 'Abonelik',
                'col_name': 'Ad',
                'col_type': 'Tür',
                'col_resource_group': 'Kaynak Grubu',
                'col_location': 'Konum',
                'col_size': 'Boyut',
                'col_state': 'Durum',
                'col_reason': 'Neden',
                'col_cost': 'Maliyet (USD/ay)',
                'download_csv': 'CSV İndir',
                'no_inactive_resources': 'İnaktif kaynak bulunamadı',
                'no_inactive_resources_for_sub': 'Bu abonelik için inaktif kaynak bulunamadı',
                'high_cost_resources': 'Yüksek Maliyetli Kaynaklar',
                'optimization_recommendations': 'Optimizasyon Önerileri',
                'summary_report': 'Özet Rapor',
                'download_html': 'HTML Raporu İndir',
                'no_report': 'Özet rapor bulunamadı. Lütfen önce analiz çalıştırın.',
                'subscription_management': 'Abonelik Yönetimi',
                'enter_subscription_id': 'Abonelik ID Girin',
                'enter_subscription_name': 'Görünen Ad Girin (isteğe bağlı)',
                'add_subscription': 'Ekle',
                'current_subscriptions': 'Mevcut Abonelikler',
                'no_subscriptions_added': 'Henüz abonelik eklenmedi. Yukarıdan en az bir abonelik ID\'si ekleyin.',
                'remove': 'Kaldır',
                'analyzing_subscription': 'Abonelik analiz ediliyor',
                'error_analyzing_subscription': 'Abonelik analiz edilirken hata',
                'deactivating_resources_for': 'Abonelik için kaynaklar devre dışı bırakılıyor',
                'azure_authentication': 'Azure Kimlik Doğrulama',
                'auth_method': 'Kimlik Doğrulama Yöntemi',
                'auth_method_service_principal': 'Service Principal',
                'auth_method_interactive': 'Tarayıcı ile Etkileşimli',
                'auth_method_default': 'Varsayılan Kimlik Bilgileri',
                'auth_method_manual': 'Manuel (Kimlik Doğrulamayı Atla)',
                'service_principal_auth': 'Service Principal Kimlik Doğrulama',
                'tenant_id': 'Tenant ID',
                'client_id': 'Client ID (App ID)',
                'client_secret': 'Client Secret',
                'connect': 'Azure\'a Bağlan',
                'login_interactive': 'Tarayıcı ile Giriş Yap',
                'login_default': 'Varsayılan Kimlik Bilgileri ile Giriş Yap',
                'skip_auth': 'Kimlik Doğrulamayı Atla',
                'manual_mode_enabled': 'Manuel mod etkinleştirildi. Şimdi abonelik ID\'lerini manuel olarak ekleyebilirsiniz.',
                'auth_error': 'Kimlik doğrulama hatası: {}',
                'connected_azure_sp': 'Service Principal kullanarak Azure\'a bağlandı',
                'connected_azure_interactive': 'Etkileşimli Tarayıcı Kimlik Doğrulama kullanarak Azure\'a bağlandı',
                'connected_azure_default': 'Varsayılan Kimlik Bilgileri kullanarak Azure\'a bağlandı',
                'interactive_auth_info': 'Bir tarayıcı penceresi açılacak. Lütfen Azure hesabınızla giriş yapın.',
                'default_auth_info': 'Ortam değişkenleri, managed identity veya Visual Studio/VSCode kimlik bilgilerini kullanır.',
                'manual_auth_warning': 'Abonelik ID\'lerini manuel olarak girmeniz gerekecek. Sınırlı işlevsellik mevcut olabilir.',
                'change_auth': 'Kimlik Doğrulamayı Değiştir',
                'auth_status_service_principal': 'Service Principal ile Bağlandı',
                'auth_status_interactive': 'Etkileşimli Tarayıcı Kimlik Doğrulama ile Bağlandı',
                'auth_status_default': 'Varsayılan Kimlik Bilgileri ile Bağlandı',
                'auth_status_manual': 'Manuel Mod (Azure Kimlik Doğrulama Yok)',
                'list_subscriptions': 'Mevcut Abonelikleri Yükle',
                'loading_subscriptions': 'Abonelikler yükleniyor...',
                'subscriptions_loaded': '{} abonelik yüklendi',
                'deactivate_options': 'Devre Dışı Bırakma Seçenekleri',
                'subscription_list_error': 'Abonelikler listelenirken hata: {}',
            }
        }
    
    def get(self, key, *args):
        """
        Belirli bir anahtar için çeviriyi döndürür.
        
        Args:
            key: Çeviri anahtarı
            args: Format parametreleri
        
        Returns:
            Çevrilen metin
        """
        # Belirtilen dilde çeviri var mı?
        translations = self.translations.get(self.language, self.translations.get('en'))
        
        # Anahtar bu dilde var mı?
        text = translations.get(key)
        
        # Yoksa İngilizce'den al
        if text is None:
            text = self.translations.get('en', {}).get(key, key)
        
        # Parametrelerle formatla
        if args:
            return text.format(*args)
        
        return text 