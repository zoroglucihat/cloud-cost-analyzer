"""
Çoklu hesaplı Azure maliyet optimizasyonu için rapor oluşturma modülü.
"""

import os
import csv
import logging
from datetime import datetime
import matplotlib.pyplot as plt
import pandas as pd

logger = logging.getLogger("ReportGenerator")

class ReportGenerator:
    def __init__(self, output_dir):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def generate_inactive_resource_report(self, inactive_resources_by_account):
        """
        İnaktif kaynaklar raporu oluşturur.
        
        Args:
            inactive_resources_by_account: Hesap bazlı inaktif kaynaklar sözlüğü
                {account_id: [resources]}
        """
        logger.info("İnaktif kaynaklar raporu oluşturuluyor...")
        
        # Tüm hesaplardan kaynakları birleştir
        all_resources = []
        for account_id, resources in inactive_resources_by_account.items():
            for resource in resources:
                # Kaynak bilgilerine hesap ID'sini ekle
                resource_copy = resource.copy()
                resource_copy['account_id'] = account_id
                all_resources.append(resource_copy)
        
        if not all_resources:
            logger.info("İnaktif kaynak bulunamadı, rapor oluşturulmadı.")
            return
        
        file_path = os.path.join(self.output_dir, "inactive_resources.csv")
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['account_id', 'name', 'type', 'resource_group', 'cost'])
            for r in all_resources:
                writer.writerow([
                    r.get('account_id'), 
                    r.get('name'), 
                    r.get('type'), 
                    r.get('resource_group'), 
                    r.get('cost')
                ])
        
        logger.info(f"İnaktif kaynaklar raporu oluşturuldu: {file_path}")
    
    def generate_high_cost_report(self, high_cost_resources_by_account):
        """
        Yüksek maliyetli kaynaklar raporu oluşturur.
        
        Args:
            high_cost_resources_by_account: Hesap bazlı yüksek maliyetli kaynaklar sözlüğü
                {account_id: [resources]}
        """
        logger.info("Yüksek maliyet raporu oluşturuluyor...")
        
        # Tüm hesaplardan kaynakları birleştir
        all_resources = []
        for account_id, resources in high_cost_resources_by_account.items():
            for resource in resources:
                resource_copy = resource.copy()
                resource_copy['account_id'] = account_id
                all_resources.append(resource_copy)
        
        if not all_resources:
            logger.info("Yüksek maliyetli kaynak bulunamadı, rapor oluşturulmadı.")
            return
        
        file_path = os.path.join(self.output_dir, "high_cost_resources.csv")
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['account_id', 'name', 'type', 'resource_group', 'cost'])
            for r in all_resources:
                writer.writerow([
                    r.get('account_id'),
                    r.get('name'), 
                    r.get('type'), 
                    r.get('resource_group'), 
                    r.get('cost')
                ])
    
    def generate_recommendations_report(self, recommendations_by_account):
        """
        Optimizasyon önerileri raporu oluşturur.
        
        Args:
            recommendations_by_account: Hesap bazlı öneriler sözlüğü
                {account_id: [recommendations]}
        """
        logger.info("Öneriler raporu oluşturuluyor...")
        
        # Tüm hesaplardan önerileri birleştir
        all_recommendations = []
        for account_id, recommendations in recommendations_by_account.items():
            for rec in recommendations:
                rec_copy = rec.copy()
                rec_copy['account_id'] = account_id
                all_recommendations.append(rec_copy)
        
        if not all_recommendations:
            logger.info("Optimizasyon önerisi bulunamadı, rapor oluşturulmadı.")
            return
        
        file_path = os.path.join(self.output_dir, "optimization_recommendations.csv")
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['account_id', 'resource_name', 'resource_type', 'issue', 'cost_impact'])
            for r in all_recommendations:
                writer.writerow([
                    r.get('account_id'),
                    r.get('resource_name'), 
                    r.get('resource_type'), 
                    r.get('issue'), 
                    r.get('cost_impact')
                ])
    
    def generate_charts(self, inactive_resources_by_account):
        """
        Analiz sonuçlarından grafikler oluşturur.
        """
        logger.info("Grafikler oluşturuluyor...")
        
        # Hesap başına inaktif kaynak sayısı grafiği
        account_ids = list(inactive_resources_by_account.keys())
        resource_counts = [len(resources) for resources in inactive_resources_by_account.values()]
        
        if not resource_counts or sum(resource_counts) == 0:
            logger.info("Grafik oluşturmak için yeterli veri yok.")
            return
        
        plt.figure(figsize=(10, 6))
        plt.bar(account_ids, resource_counts)
        plt.title('Hesap Başına İnaktif Kaynak Sayısı')
        plt.xlabel('Hesap ID')
        plt.ylabel('Kaynak Sayısı')
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        chart_path = os.path.join(self.output_dir, "accounts_inactive_resources.png")
        plt.savefig(chart_path)
        plt.close()
        
        logger.info(f"Hesap bazlı inaktif kaynaklar grafiği oluşturuldu: {chart_path}")
    
    def generate_summary_report(self, inactive_resources_by_account, high_cost_resources_by_account, recommendations_by_account, account_configs):
        """
        Özet HTML raporu oluşturur.
        
        Args:
            inactive_resources_by_account: Hesap bazlı inaktif kaynaklar
            high_cost_resources_by_account: Hesap bazlı yüksek maliyetli kaynaklar
            recommendations_by_account: Hesap bazlı öneriler
            account_configs: Hesap yapılandırmaları {account_id: AccountConfig}
        """
        logger.info("Özet rapor oluşturuluyor...")
        
        # Hesap bazlı istatistikler
        account_stats = {}
        
        total_inactive = 0
        total_high_cost = 0
        total_recommendations = 0
        total_inactive_cost = 0
        total_high_cost_cost = 0
        
        for account_id, resources in inactive_resources_by_account.items():
            if account_id not in account_stats:
                account_stats[account_id] = {
                    'inactive_count': 0,
                    'high_cost_count': 0,
                    'recommendations_count': 0,
                    'inactive_cost': 0,
                    'high_cost_cost': 0,
                    'display_name': account_configs.get(account_id, {}).get('display_name', account_id)
                }
            
            account_stats[account_id]['inactive_count'] = len(resources)
            account_stats[account_id]['inactive_cost'] = sum(r.get('cost', 0) for r in resources)
            
            total_inactive += len(resources)
            total_inactive_cost += account_stats[account_id]['inactive_cost']
        
        for account_id, resources in high_cost_resources_by_account.items():
            if account_id not in account_stats:
                account_stats[account_id] = {
                    'inactive_count': 0,
                    'high_cost_count': 0,
                    'recommendations_count': 0,
                    'inactive_cost': 0,
                    'high_cost_cost': 0,
                    'display_name': account_configs.get(account_id, {}).get('display_name', account_id)
                }
            
            account_stats[account_id]['high_cost_count'] = len(resources)
            account_stats[account_id]['high_cost_cost'] = sum(r.get('cost', 0) for r in resources)
            
            total_high_cost += len(resources)
            total_high_cost_cost += account_stats[account_id]['high_cost_cost']
        
        for account_id, recommendations in recommendations_by_account.items():
            if account_id not in account_stats:
                account_stats[account_id] = {
                    'inactive_count': 0,
                    'high_cost_count': 0,
                    'recommendations_count': 0,
                    'inactive_cost': 0,
                    'high_cost_cost': 0,
                    'display_name': account_configs.get(account_id, {}).get('display_name', account_id)
                }
            
            account_stats[account_id]['recommendations_count'] = len(recommendations)
            total_recommendations += len(recommendations)
        
        # HTML içeriğini oluştur
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Azure Çoklu Hesap Maliyet Optimizasyonu</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .summary {{ background-color: #e9f7ff; padding: 15px; border-radius: 5px; }}
                .account-section {{ margin-top: 30px; }}
            </style>
        </head>
        <body>
            <h1>Azure Çoklu Hesap Maliyet Optimizasyonu Raporu</h1>
            <p>Oluşturulma: {datetime.now().strftime('%d-%m-%Y %H:%M')}</p>
            
            <div class="summary">
                <h2>Genel Özet</h2>
                <p>Analiz edilen hesap sayısı: {len(account_stats)}</p>
                <p>Toplam inaktif kaynak sayısı: {total_inactive}</p>
                <p>Toplam yüksek maliyetli kaynak sayısı: {total_high_cost}</p>
                <p>Toplam öneri sayısı: {total_recommendations}</p>
                <p>İnaktif kaynakların toplam maliyeti: ${total_inactive_cost:.2f}/ay</p>
                <p>Yüksek maliyetli kaynakların toplam maliyeti: ${total_high_cost_cost:.2f}/ay</p>
            </div>
            
            <h2>Hesap Bazlı Özet</h2>
            <table>
                <tr>
                    <th>Hesap</th>
                    <th>İnaktif Kaynaklar</th>
                    <th>Yüksek Maliyetli Kaynaklar</th>
                    <th>Öneriler</th>
                    <th>İnaktif Maliyeti (USD/ay)</th>
                    <th>Yüksek Maliyet (USD/ay)</th>
                </tr>
                {''.join([f'''
                <tr>
                    <td>{stats['display_name']}</td>
                    <td>{stats['inactive_count']}</td>
                    <td>{stats['high_cost_count']}</td>
                    <td>{stats['recommendations_count']}</td>
                    <td>${stats['inactive_cost']:.2f}</td>
                    <td>${stats['high_cost_cost']:.2f}</td>
                </tr>
                ''' for account_id, stats in account_stats.items()])}
            </table>
            
            <h2>En Yüksek Maliyetli İnaktif Kaynaklar</h2>
            <table>
                <tr>
                    <th>Hesap</th>
                    <th>Kaynak Adı</th>
                    <th>Tür</th>
                    <th>Maliyet (USD/ay)</th>
                </tr>
        """
        
        # Tüm hesaplardan en yüksek maliyetli inaktif kaynakları topla
        all_inactive = []
        for account_id, resources in inactive_resources_by_account.items():
            for r in resources:
                r_copy = r.copy()
                r_copy['account_id'] = account_id
                r_copy['account_name'] = account_stats[account_id]['display_name']
                all_inactive.append(r_copy)
        
        # Maliyete göre sırala
        all_inactive.sort(key=lambda x: x.get('cost', 0), reverse=True)
        
        # İlk 10 kaynağı göster
        for r in all_inactive[:10]:
            html_content += f"""
                <tr>
                    <td>{r['account_name']}</td>
                    <td>{r.get('name', 'Bilinmiyor')}</td>
                    <td>{r.get('type', 'Bilinmiyor')}</td>
                    <td>${r.get('cost', 0):.2f}</td>
                </tr>
            """
        
        html_content += """
            </table>
            
            <p style="margin-top: 30px;"><em>Bu rapor, Azure kaynaklarınızın kullanımını optimize etmenize yardımcı olmak için oluşturulmuştur. 
            Herhangi bir değişiklik yapmadan önce, önerilen eylemlerin etkilerini değerlendirin.</em></p>
        </body>
        </html>
        """
        
        file_path = os.path.join(self.output_dir, "summary_report.html")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"Özet rapor oluşturuldu: {file_path}")
    
    def generate_visualization(self, inactive_resources_by_account):
        """
        Çoklu hesap bazlı görselleştirmeler oluşturur.
        """
        logger.info("Görselleştirmeler oluşturuluyor...")
        # Hesap başına inaktif kaynak dağılımı grafiği
        try:
            if not inactive_resources_by_account:
                return
                
            # Hesap başına maliyet grafiği
            account_costs = {}
            for account_id, resources in inactive_resources_by_account.items():
                account_costs[account_id] = sum(r.get('cost', 0) for r in resources)
            
            plt.figure(figsize=(10, 6))
            plt.bar(account_costs.keys(), account_costs.values())
            plt.title('Hesap Başına İnaktif Kaynak Maliyeti')
            plt.xlabel('Hesap ID')
            plt.ylabel('Maliyet (USD/ay)')
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            chart_path = os.path.join(self.output_dir, "accounts_cost.png")
            plt.savefig(chart_path)
            plt.close()
            
            logger.info(f"Hesap bazlı maliyet grafiği oluşturuldu: {chart_path}")
            
        except Exception as e:
            logger.error(f"Görselleştirmeler oluşturulurken hata: {str(e)}")
