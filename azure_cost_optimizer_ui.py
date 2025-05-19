import streamlit as st
import os
import pandas as pd
import matplotlib.pyplot as plt
from io import StringIO
import time
import tempfile
import datetime
from modules.config import AppConfig, AccountConfig
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
from modules.i18n import Translator
from azure.identity import ClientSecretCredential, DefaultAzureCredential, InteractiveBrowserCredential

# Çevirici başlat
translator = Translator()
t = translator.get

def main():
    st.set_page_config(
        page_title="Azure Cost Optimizer", 
        page_icon="💰",
        layout="wide"
    )
    
    # Dil seçimi
    languages = translator.LANGUAGES
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("Azure Cost Optimizer")
        st.caption(t("app_subtitle"))
    with col2:
        selected_lang = st.selectbox(
            t("select_language"),
            options=list(languages.keys()),
            format_func=lambda x: languages[x],
            index=0
        )
        translator.language = selected_lang
    
    # Oturum durumu
    if 'subscription_list' not in st.session_state:
        st.session_state.subscription_list = []
    
    if 'analysis_complete' not in st.session_state:
        st.session_state.analysis_complete = False
        st.session_state.inactive_resources = {}
        st.session_state.high_cost_resources = {}
        st.session_state.recommendations = {}
        st.session_state.output_dir = "reports"
    
    if 'credential' not in st.session_state:
        st.session_state.credential = None
        st.session_state.auth_method = None
    
    # Kimlik doğrulama ve client manager
    if 'client_manager' not in st.session_state:
        # Kimlik Doğrulama Seçimi 
        st.header(t("azure_authentication"))
        
        auth_methods = ["service_principal", "interactive", "default", "manual"]
        auth_method = st.radio(
            t("auth_method"),
            options=auth_methods,
            format_func=lambda x: t(f"auth_method_{x}"),
            horizontal=True
        )
        
        if auth_method == "service_principal":
            # Service Principal ile kimlik doğrulama
            with st.form("sp_auth_form"):
                st.subheader(t("service_principal_auth"))
                tenant_id = st.text_input(t("tenant_id"), type="password")
                client_id = st.text_input(t("client_id"), type="password")
                client_secret = st.text_input(t("client_secret"), type="password")
                
                submit = st.form_submit_button(t("connect"))
                
                if submit and tenant_id and client_id and client_secret:
                    try:
                        with st.spinner(t("connecting_azure")):
                            credential = ClientSecretCredential(
                                tenant_id=tenant_id,
                                client_id=client_id,
                                client_secret=client_secret
                            )
                            
                            # Test the credential
                            from azure.mgmt.resource import ResourceManagementClient
                            ResourceManagementClient(credential, "00000000-0000-0000-0000-000000000000")
                            
                            st.session_state.credential = credential
                            st.session_state.auth_method = "service_principal"
                            st.session_state.client_manager = AzureClientManager(credential)
                            
                            st.success(t("connected_azure_sp"))
                            st.rerun()
                    except Exception as e:
                        st.error(t("auth_error", str(e)))
        
        elif auth_method == "interactive":
            # Etkileşimli tarayıcı kimlik doğrulama
            if st.button(t("login_interactive")):
                try:
                    with st.spinner(t("connecting_azure")):
                        credential = InteractiveBrowserCredential()
                        
                        # Test the credential
                        from azure.mgmt.resource import ResourceManagementClient
                        ResourceManagementClient(credential, "00000000-0000-0000-0000-000000000000")
                        
                        st.session_state.credential = credential
                        st.session_state.auth_method = "interactive"
                        st.session_state.client_manager = AzureClientManager(credential)
                        
                        st.success(t("connected_azure_interactive"))
                        st.rerun()
                except Exception as e:
                    st.error(t("auth_error", str(e)))
            
            st.info(t("interactive_auth_info"))
        
        elif auth_method == "default":
            # DefaultAzureCredential kullanarak kimlik doğrulama
            if st.button(t("login_default")):
                try:
                    with st.spinner(t("connecting_azure")):
                        credential = DefaultAzureCredential()
                        
                        # Test the credential
                        from azure.mgmt.resource import ResourceManagementClient
                        ResourceManagementClient(credential, "00000000-0000-0000-0000-000000000000")
                        
                        st.session_state.credential = credential
                        st.session_state.auth_method = "default"
                        st.session_state.client_manager = AzureClientManager(credential)
                        
                        st.success(t("connected_azure_default"))
                        st.rerun()
                except Exception as e:
                    st.error(t("auth_error", str(e)))
            
            st.info(t("default_auth_info"))
        
        elif auth_method == "manual":
            # Manuel kimlik doğrulama atlama
            if st.button(t("skip_auth")):
                st.session_state.client_manager = "manual"
                st.success(t("manual_mode_enabled"))
                st.rerun()
            
            st.warning(t("manual_auth_warning"))
        
        # Ana uygulamayı göstermeden önce durdur
        st.stop()
    
    # Ana uygulama
    # Yan panel
    with st.sidebar:
        st.header(t("settings"))
        
        # Kimlik bilgilerini değiştir
        if st.button(t("change_auth")):
            # Kimlik doğrulama durumunu sıfırla
            st.session_state.credential = None
            st.session_state.auth_method = None
            st.session_state.client_manager = None
            st.rerun()
        
        # Bağlantı durumunu göster
        if st.session_state.auth_method:
            st.success(t(f"auth_status_{st.session_state.auth_method}"))
        elif st.session_state.client_manager == "manual":
            st.warning(t("auth_status_manual"))
        
        # Abonelik yönetimi
        st.subheader(t("subscription_management"))
        
        # Otomatik abonelik listeleme özelliği (sadece kimlik doğrulaması yapıldığında)
        if isinstance(st.session_state.client_manager, AzureClientManager):
            if st.button(t("list_subscriptions")):
                try:
                    with st.spinner(t("loading_subscriptions")):
                        subscriptions = st.session_state.client_manager.list_subscriptions()
                        st.session_state.subscription_list = [
                            {"id": sub.subscription_id, "name": sub.display_name} 
                            for sub in subscriptions
                        ]
                        st.success(t("subscriptions_loaded", len(subscriptions)))
                        st.rerun()
                except Exception as e:
                    st.error(t("subscription_list_error", str(e)))
        
        # Yeni abonelik ekleme
        col1, col2 = st.columns([3, 1])
        with col1:
            new_sub_id = st.text_input(t("enter_subscription_id"), key="new_sub_id")
            new_sub_name = st.text_input(t("enter_subscription_name"), key="new_sub_name", 
                                         value=f"Abonelik {len(st.session_state.subscription_list) + 1}" if new_sub_id else "")
        with col2:
            add_btn = st.button(t("add_subscription"))
            if add_btn and new_sub_id:
                st.session_state.subscription_list.append({
                    "id": new_sub_id,
                    "name": new_sub_name or new_sub_id
                })
                # Metin alanını temizle
                st.session_state.new_sub_id = ""
                st.rerun()
        
        # Mevcut abonelikler
        st.subheader(t("current_subscriptions"))
        if not st.session_state.subscription_list:
            st.info(t("no_subscriptions_added"))
        else:
            for i, sub in enumerate(st.session_state.subscription_list):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(f"{sub['name']} ({sub['id']})")
                with col2:
                    if st.button(t("remove"), key=f"remove_{i}"):
                        st.session_state.subscription_list.pop(i)
                        st.rerun()
        
        # Analiz parametreleri
        st.subheader(t("analysis_parameters"))
        
        days_inactive = st.slider(
            t("days_inactive"), 
            min_value=1, 
            max_value=90, 
            value=30,
            help=t("days_inactive_help")
        )
        
        cost_threshold = st.number_input(
            t("cost_threshold"), 
            min_value=1.0, 
            max_value=1000.0, 
            value=10.0,
            help=t("cost_threshold_help")
        )
        
        output_dir = st.text_input(
            t("output_dir"), 
            "reports",
            help=t("output_dir_help")
        )
        
        st.session_state.output_dir = output_dir
        
        # Analiz butonları
        st.subheader(t("actions"))
        
        analyze_button = st.button(
            t("analyze_button"), 
            disabled=not st.session_state.subscription_list,
            use_container_width=True
        )
        
        deactivate_options = st.expander(t("deactivate_options"))
        with deactivate_options:
            dry_run = st.checkbox(
                t("dry_run"), 
                value=True,
                help=t("dry_run_help")
            )
            
            deactivate_button = st.button(
                t("deactivate_button"),
                disabled=not (st.session_state.analysis_complete and st.session_state.inactive_resources),
                help=t("deactivate_help")
            )
    
    # Ana içerik
    if analyze_button:
        with st.spinner(t("analyzing")):
            try:
                # Config oluştur
                config = AppConfig(output_dir=output_dir)
                
                # Abonelik yapılandırmalarını oluştur
                for sub in st.session_state.subscription_list:
                    config.accounts.append(AccountConfig(
                        subscription_id=sub["id"], 
                        display_name=sub["name"],
                        days_inactive=days_inactive,
                        cost_threshold=cost_threshold
                    ))
                
                # Client manager oluştur (manuel modda)
                client_manager = AzureClientManager()
                
                # Her abonelik için analiz yap
                inactive_resources = {}
                high_cost_resources = {}
                recommendations = {}
                
                for account in config.accounts:
                    sub_id = account.subscription_id
                    
                    st.info(f"{t('analyzing_subscription')}: {account.display_name} ({sub_id})")
                    
                    try:
                        # Azure istemcisini al
                        azure_client = client_manager.get_client(sub_id)
                        
                        # Analizörler
                        resource_analyzer = ResourceAnalyzer(azure_client)
                        vm_analyzer = VMAnalyzer(azure_client, account)
                        app_service_analyzer = AppServiceAnalyzer(azure_client, account)
                        storage_analyzer = StorageAnalyzer(azure_client, account)
                        sql_analyzer = SQLAnalyzer(azure_client, account)
                        cosmos_analyzer = CosmosDBAnalyzer(azure_client, account)
                        aks_analyzer = AKSAnalyzer(azure_client, account)
                        
                        # Kaynakları al ve analiz et
                        all_resources = resource_analyzer.get_all_resources()
                        
                        # İnaktif kaynak analizi
                        vm_inactive = vm_analyzer.find_inactive_vms(all_resources)
                        app_inactive = app_service_analyzer.find_inactive_app_services(all_resources)
                        storage_inactive = storage_analyzer.find_inactive_storage_accounts(all_resources)
                        sql_inactive = sql_analyzer.find_inactive_sql_databases(all_resources)
                        cosmos_inactive = cosmos_analyzer.find_inactive_cosmos_dbs(all_resources)
                        aks_inactive = aks_analyzer.find_inactive_aks_clusters(all_resources)
                        
                        inactive = vm_inactive + app_inactive + storage_inactive + sql_inactive + cosmos_inactive + aks_inactive
                        
                        # Maliyet analizi
                        cost_analyzer = CostAnalyzer(azure_client, account)
                        
                        # İnaktif kaynaklara maliyet bilgisi ekle
                        for resource in inactive:
                            resource_id = resource.get('id')
                            if resource_id:
                                resource['cost'] = cost_analyzer.get_resource_cost(resource_id)
                        
                        # Yüksek maliyetli kaynakları bul
                        high_cost = cost_analyzer.find_high_cost_resources(all_resources)
                        
                        # Optimizer
                        recommender = OptimizationRecommender(azure_client, account)
                        optimize_recommendations = recommender.generate_recommendations(
                            all_resources, inactive, high_cost
                        )
                        
                        # Sonuçları kaydet
                        inactive_resources[sub_id] = inactive
                        high_cost_resources[sub_id] = high_cost
                        recommendations[sub_id] = optimize_recommendations
                        
                    except Exception as e:
                        st.error(f"{t('error_analyzing_subscription')}: {sub_id} - {str(e)}")
                
                # Raporları oluştur
                with st.spinner(t("generating_reports")):
                    reporter = ReportGenerator(output_dir)
                    reporter.generate_inactive_resource_report(inactive_resources)
                    reporter.generate_high_cost_report(high_cost_resources)
                    reporter.generate_recommendations_report(recommendations)
                    reporter.generate_charts(inactive_resources)
                    
                    # Hesap konfigürasyonlarını sözlük formatına dönüştür
                    account_configs = {acc.subscription_id: {
                        'display_name': acc.display_name,
                        'days_inactive': acc.days_inactive,
                        'cost_threshold': acc.cost_threshold
                    } for acc in config.accounts}
                    
                    reporter.generate_summary_report(
                        inactive_resources, 
                        high_cost_resources, 
                        recommendations,
                        account_configs
                    )
                    
                    reporter.generate_visualization(inactive_resources)
                
                # Oturum verilerini kaydet
                st.session_state.inactive_resources = inactive_resources
                st.session_state.high_cost_resources = high_cost_resources
                st.session_state.recommendations = recommendations
                st.session_state.analysis_complete = True
                
                st.success(t("analysis_success"))
                
            except Exception as e:
                st.error(f"{t('error_analysis')}: {str(e)}")
    
    # Devre dışı bırakma işlemi
    if deactivate_button:
        with st.spinner(t("deactivating_resources")):
            try:
                success_count = 0
                error_count = 0
                
                for sub_id, resources in st.session_state.inactive_resources.items():
                    if not resources:
                        continue
                        
                    st.info(f"{t('deactivating_resources_for')}: {sub_id}")
                    
                    try:
                        azure_client = AzureClientManager().get_client(sub_id)
                        
                        for resource in resources:
                            resource_id = resource.get('id')
                            resource_name = resource.get('name')
                            resource_type = resource.get('type', '').lower()
                            
                            if dry_run:
                                st.write(f"[SİMÜLASYON] {resource_name} devre dışı bırakılacaktı")
                                success_count += 1
                                continue
                            
                            try:
                                # Kaynak türüne göre devre dışı bırakma işlemi
                                if 'microsoft.compute/virtualmachines' in resource_type:
                                    # VM'i deallocate et
                                    resource_group = azure_client.extract_resource_group(resource_id)
                                    azure_client.compute_client.virtual_machines.deallocate(
                                        resource_group, resource_name)
                                    st.write(f"✅ VM deallocate: {resource_name}")
                                    success_count += 1
                                
                                elif 'microsoft.web/sites' in resource_type:
                                    # App Service'i durdur
                                    resource_group = azure_client.extract_resource_group(resource_id)
                                    azure_client.web_client.web_apps.stop(resource_group, resource_name)
                                    st.write(f"✅ App Service durduruldu: {resource_name}")
                                    success_count += 1
                                
                                # Diğer kaynak türleri için benzer işlemler eklenebilir
                                else:
                                    st.warning(f"❓ Bu kaynak türü için işlem desteklenmiyor: {resource_type} - {resource_name}")
                                
                            except Exception as e:
                                st.error(f"❌ Kaynak devre dışı bırakılırken hata: {resource_name} - {str(e)}")
                                error_count += 1
                        
                    except Exception as e:
                        st.error(f"❌ Abonelik için hata: {sub_id} - {str(e)}")
                        error_count += 1
                
                if dry_run:
                    st.success(f"{t('deactivation_simulation_success')} - {success_count} kaynak simüle edildi")
                else:
                    st.success(f"{t('deactivation_success')} - {success_count} başarılı, {error_count} hatalı")
                    
            except Exception as e:
                st.error(f"{t('error_deactivation')}: {str(e)}")
    
    # Sonuçları göster (analiz tamamlandığında)
    if st.session_state.analysis_complete:
        tab1, tab2, tab3, tab4 = st.tabs([
            t("tab_inactive"), 
            t("tab_high_cost"), 
            t("tab_recommendations"),
            t("tab_report")
        ])
        
        with tab1:
            st.subheader(t("inactive_resources"))
            
            # Abonelik seçimi
            sub_ids = list(st.session_state.inactive_resources.keys())
            
            if not sub_ids:
                st.info(t("no_inactive_resources"))
            else:
                if len(sub_ids) > 1:
                    selected_sub = st.selectbox(
                        t("select_sub_to_view"),
                        options=["all"] + sub_ids,
                        format_func=lambda x: t("all_subscriptions") if x == "all" else next(
                            (sub["name"] for sub in st.session_state.subscription_list if sub["id"] == x),
                            x
                        ),
                        key="inactive_sub_select"
                    )
                else:
                    selected_sub = sub_ids[0]
                
                # Tabloda gösterilecek kaynakları belirle
                if selected_sub == "all":
                    # Tüm aboneliklerden kaynakları birleştir
                    all_resources = []
                    for sub_id, resources in st.session_state.inactive_resources.items():
                        sub_name = next((sub["name"] for sub in st.session_state.subscription_list if sub["id"] == sub_id), sub_id)
                        for resource in resources:
                            resource_copy = resource.copy()
                            resource_copy['subscription'] = sub_name
                            all_resources.append(resource_copy)
                    
                    # DataFrame oluştur
                    if all_resources:
                        df = pd.DataFrame(all_resources)
                        # Gereksiz sütunları kaldır
                        df = df[['subscription', 'name', 'type', 'resource_group', 'location', 'size', 'state', 'reason', 'cost']]
                        # Sütun adlarını çevir
                        df.columns = [t("col_subscription"), t("col_name"), t("col_type"), t("col_resource_group"), 
                                     t("col_location"), t("col_size"), t("col_state"), t("col_reason"), t("col_cost")]
                        
                        st.dataframe(df, use_container_width=True)
                        
                        # CSV indirme düğmesi
                        csv = df.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label=t("download_csv"),
                            data=csv,
                            file_name=f"inactive_resources_{datetime.datetime.now().strftime('%Y%m%d')}.csv",
                            mime="text/csv"
                        )
                    else:
                        st.info(t("no_inactive_resources"))
                
                elif selected_sub and selected_sub in st.session_state.inactive_resources:
                    resources = st.session_state.inactive_resources[selected_sub]
                    
                    if resources:
                        df = pd.DataFrame(resources)
                        # Gereksiz sütunları kaldır
                        df = df[['name', 'type', 'resource_group', 'location', 'size', 'state', 'reason', 'cost']]
                        # Sütun adlarını çevir
                        df.columns = [t("col_name"), t("col_type"), t("col_resource_group"), t("col_location"), 
                                     t("col_size"), t("col_state"), t("col_reason"), t("col_cost")]
                        
                        st.dataframe(df, use_container_width=True)
                        
                        # CSV indirme düğmesi
                        csv = df.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label=t("download_csv"),
                            data=csv,
                            file_name=f"inactive_resources_{selected_sub}_{datetime.datetime.now().strftime('%Y%m%d')}.csv",
                            mime="text/csv"
                        )
                    else:
                        st.info(t("no_inactive_resources_for_sub"))
        
        with tab2:
            st.subheader(t("high_cost_resources"))
            
            # Toplam yüksek maliyetli kaynak sayısı
            total_high_cost = sum(len(resources) for resources in st.session_state.high_cost_resources.values())
            
            if total_high_cost > 0:
                # Abonelik seçimi
                sub_ids = list(st.session_state.high_cost_resources.keys())
                
                if len(sub_ids) > 1:
                    selected_sub = st.selectbox(
                        t("select_sub_to_view"),
                        options=["all"] + sub_ids,
                        format_func=lambda x: t("all_subscriptions") if x == "all" else next(
                            (sub["name"] for sub in st.session_state.subscription_list if sub["id"] == x),
                            x
                        ),
                        key="high_cost_sub_select"
                    )
                else:
                    selected_sub = sub_ids[0] if sub_ids else None
                
                # Tabloda gösterilecek kaynakları belirle
                if selected_sub == "all":
                    # Tüm aboneliklerden kaynakları birleştir
                    all_resources = []
                    for sub_id, resources in st.session_state.high_cost_resources.items():
                        sub_name = next((sub["name"] for sub in st.session_state.subscription_list if sub["id"] == sub_id), sub_id)
                        for resource in resources:
                            resource_copy = resource.copy()
                            resource_copy['subscription'] = sub_name
                            all_resources.append(resource_copy)
                    
                    # DataFrame oluştur
                    if all_resources:
                        df = pd.DataFrame(all_resources)
                        # Gereksiz sütunları kaldır
                        columns = ['subscription', 'name', 'type', 'resource_group', 'location', 'cost']
                        df = df[columns]
                        # Sütun adlarını çevir
                        df.columns = [t("col_subscription"), t("col_name"), t("col_type"), 
                                      t("col_resource_group"), t("col_location"), t("col_cost")]
                        
                        st.dataframe(df, use_container_width=True)
                        
                        # CSV indirme düğmesi
                        csv = df.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label=t("download_csv"),
                            data=csv,
                            file_name=f"high_cost_resources_{datetime.datetime.now().strftime('%Y%m%d')}.csv",
                            mime="text/csv"
                        )
                    else:
                        st.info(t("no_high_cost_resources"))
                
                elif selected_sub and selected_sub in st.session_state.high_cost_resources:
                    resources = st.session_state.high_cost_resources[selected_sub]
                    
                    if resources:
                        df = pd.DataFrame(resources)
                        # Gereksiz sütunları kaldır
                        columns = ['name', 'type', 'resource_group', 'location', 'cost']
                        df = df[columns]
                        # Sütun adlarını çevir
                        df.columns = [t("col_name"), t("col_type"), t("col_resource_group"), 
                                      t("col_location"), t("col_cost")]
                        
                        st.dataframe(df, use_container_width=True)
                        
                        # CSV indirme düğmesi
                        csv = df.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label=t("download_csv"),
                            data=csv,
                            file_name=f"high_cost_resources_{selected_sub}_{datetime.datetime.now().strftime('%Y%m%d')}.csv",
                            mime="text/csv"
                        )
                    else:
                        st.info(t("no_high_cost_resources_for_sub"))
            else:
                st.info(t("no_high_cost_resources"))
        
        with tab3:
            st.subheader(t("optimization_recommendations"))
            
            # Toplam öneri sayısı
            total_recommendations = sum(len(recommendations) for recommendations in st.session_state.recommendations.values())
            
            if total_recommendations > 0:
                # Abonelik seçimi
                sub_ids = list(st.session_state.recommendations.keys())
                
                if len(sub_ids) > 1:
                    selected_sub = st.selectbox(
                        t("select_sub_to_view"),
                        options=["all"] + sub_ids,
                        format_func=lambda x: t("all_subscriptions") if x == "all" else next(
                            (sub["name"] for sub in st.session_state.subscription_list if sub["id"] == x),
                            x
                        ),
                        key="recommendations_sub_select"
                    )
                else:
                    selected_sub = sub_ids[0] if sub_ids else None
                
                # Tabloda gösterilecek önerileri belirle
                if selected_sub == "all":
                    # Tüm aboneliklerden önerileri birleştir
                    all_recommendations = []
                    for sub_id, recommendations in st.session_state.recommendations.items():
                        sub_name = next((sub["name"] for sub in st.session_state.subscription_list if sub["id"] == sub_id), sub_id)
                        for rec in recommendations:
                            rec_copy = rec.copy()
                            rec_copy['subscription'] = sub_name
                            all_recommendations.append(rec_copy)
                    
                    # DataFrame oluştur
                    if all_recommendations:
                        df = pd.DataFrame(all_recommendations)
                        # Sütunları düzenle
                        columns = ['subscription', 'resource_name', 'resource_type', 'issue', 'recommendation', 'cost_impact']
                        for col in columns:
                            if col not in df.columns:
                                df[col] = ""
                        df = df[columns]
                        
                        # Sütun adlarını çevir
                        df.columns = ['Abonelik', 'Kaynak Adı', 'Kaynak Türü', 'Sorun', 'Öneri', 'Maliyet Etkisi (USD/ay)']
                        
                        st.dataframe(df, use_container_width=True)
                        
                        # CSV indirme düğmesi
                        csv = df.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label=t("download_csv"),
                            data=csv,
                            file_name=f"recommendations_{datetime.datetime.now().strftime('%Y%m%d')}.csv",
                            mime="text/csv"
                        )
                    else:
                        st.info("Öneri bulunamadı.")
                
                elif selected_sub and selected_sub in st.session_state.recommendations:
                    recommendations = st.session_state.recommendations[selected_sub]
                    
                    if recommendations:
                        df = pd.DataFrame(recommendations)
                        # Sütunları düzenle
                        columns = ['resource_name', 'resource_type', 'issue', 'recommendation', 'cost_impact']
                        for col in columns:
                            if col not in df.columns:
                                df[col] = ""
                        df = df[columns]
                        
                        # Sütun adlarını çevir
                        df.columns = ['Kaynak Adı', 'Kaynak Türü', 'Sorun', 'Öneri', 'Maliyet Etkisi (USD/ay)']
                        
                        st.dataframe(df, use_container_width=True)
                        
                        # CSV indirme düğmesi
                        csv = df.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label=t("download_csv"),
                            data=csv,
                            file_name=f"recommendations_{selected_sub}_{datetime.datetime.now().strftime('%Y%m%d')}.csv",
                            mime="text/csv"
                        )
                    else:
                        st.info("Bu abonelik için öneri bulunamadı.")
            else:
                st.info("Hiç öneri bulunamadı.")
        
        with tab4:
            st.subheader(t("summary_report"))
            
            # Rapor dosyasını oku ve göster
            report_path = os.path.join(st.session_state.output_dir, "summary_report.html")
            
            if os.path.exists(report_path):
                with open(report_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                
                st.components.v1.html(html_content, height=600, scrolling=True)
                
                # Raporu indirme düğmesi
                st.download_button(
                    label=t("download_html"),
                    data=html_content,
                    file_name=f"azure_optimization_report_{datetime.datetime.now().strftime('%Y%m%d')}.html",
                    mime="text/html"
                )
            else:
                st.error(t("no_report"))

if __name__ == "__main__":
    main() 