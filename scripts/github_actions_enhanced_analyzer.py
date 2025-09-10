#!/usr/bin/env python3
"""
GitHub Actions Enhanced Marketplace Analyzer
Uses the actual Suppliersourcing_for_marketplaces system with real data
"""

import os
import sys
import pandas as pd
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import re
from urllib.parse import urlparse
import time

class GitHubActionsMarketplaceAnalyzer:
    def __init__(self, marketplace_url, max_suppliers=20):
        self.marketplace_url = marketplace_url
        self.max_suppliers = max_suppliers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def load_japanese_stores_database(self):
        """Load the actual Japanese stores database"""
        try:
            csv_path = "Storeleads_shopify/all_japan_stores_unlimited.csv"
            if os.path.exists(csv_path):
                df = pd.read_csv(csv_path)
                print(f"✅ Loaded {len(df)} Japanese stores from database")
                return df
            else:
                print(f"❌ Database file not found: {csv_path}")
                return None
        except Exception as e:
            print(f"❌ Error loading database: {e}")
            return None
    
    def analyze_marketplace(self):
        """Comprehensive marketplace analysis"""
        print(f"🔍 Analyzing marketplace: {self.marketplace_url}")
        
        try:
            response = self.session.get(self.marketplace_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract basic information
            analysis_result = {
                'url': self.marketplace_url,
                'title': self._extract_title(soup),
                'description': self._extract_description(soup),
                'categories': self._extract_categories(soup),
                'price_analysis': self._analyze_prices(soup),
                'brand_analysis': self._analyze_brands(soup),
                'language': self._detect_language(soup),
                'country': self._detect_country(soup),
                'analysis_timestamp': datetime.now().isoformat()
            }
            
            print(f"✅ Marketplace analysis completed")
            print(f"   Title: {analysis_result['title']}")
            print(f"   Categories: {', '.join(analysis_result['categories'][:5])}")
            print(f"   Language: {analysis_result['language']}")
            
            return analysis_result
            
        except Exception as e:
            print(f"❌ Error analyzing marketplace: {e}")
            return None
    
    def _extract_title(self, soup):
        """Extract marketplace title"""
        title_elem = soup.find('title')
        return title_elem.text.strip() if title_elem else "Unknown Marketplace"
    
    def _extract_description(self, soup):
        """Extract marketplace description"""
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            return meta_desc.get('content', '')[:200]
        
        # Fallback: extract from first paragraph
        first_p = soup.find('p')
        if first_p:
            return first_p.get_text()[:200]
        
        return ""
    
    def _extract_categories(self, soup):
        """Extract product categories from marketplace"""
        categories = []
        text_content = soup.get_text().lower()
        
        # Enhanced category keywords based on the actual system
        category_keywords = {
            'fashion': ['fashion', 'clothing', 'apparel', 'dress', 'shirt', 'pants', 'denim', 'jeans'],
            'beauty': ['beauty', 'cosmetics', 'makeup', 'skincare', 'perfume', 'skincare device', 'facial'],
            'electronics': ['electronics', 'phone', 'laptop', 'computer', 'gadget', 'tech'],
            'home': ['home', 'furniture', 'decor', 'kitchen', 'bedroom', 'living'],
            'sports': ['sports', 'fitness', 'outdoor', 'exercise', 'athletic', 'cycling', 'winter sports'],
            'jewelry': ['jewelry', 'watch', 'necklace', 'ring', 'bracelet', 'accessories'],
            'books': ['books', 'reading', 'literature', 'novel', 'textbook'],
            'toys': ['toys', 'games', 'children', 'kids', 'play'],
            'automotive': ['car', 'auto', 'vehicle', 'parts', 'automotive'],
            'health': ['health', 'medical', 'wellness', 'supplement', 'pharmacy'],
            'pets': ['pet', 'dog', 'cat', 'animal', 'pet food', 'pet toy', 'pet care']
        }
        
        for category, keywords in category_keywords.items():
            if any(keyword in text_content for keyword in keywords):
                categories.append(category)
        
        return categories[:10]  # Limit to top 10 categories
    
    def _analyze_prices(self, soup):
        """Analyze price patterns in the marketplace"""
        price_patterns = [
            r'\$[\d,]+\.?\d*',  # USD
            r'€[\d,]+\.?\d*',   # EUR
            r'£[\d,]+\.?\d*',   # GBP
            r'¥[\d,]+',         # JPY/CNY
            r'₹[\d,]+\.?\d*',   # INR
        ]
        
        prices = []
        text_content = soup.get_text()
        
        for pattern in price_patterns:
            matches = re.findall(pattern, text_content)
            for match in matches:
                try:
                    # Extract numeric value
                    numeric_value = re.sub(r'[^\d.]', '', match)
                    if numeric_value:
                        price = float(numeric_value)
                        if 1 <= price <= 50000:  # Reasonable price range
                            prices.append(price)
                except:
                    continue
        
        if prices:
            return {
                'average_price': round(sum(prices) / len(prices), 2),
                'min_price': round(min(prices), 2),
                'max_price': round(max(prices), 2),
                'price_count': len(prices),
                'currency_detected': self._detect_currency(soup)
            }
        
        return {
            'average_price': 0,
            'min_price': 0,
            'max_price': 0,
            'price_count': 0,
            'currency_detected': 'USD'
        }
    
    def _analyze_brands(self, soup):
        """Analyze brand presence and positioning"""
        text_content = soup.get_text().lower()
        
        # Look for luxury indicators
        luxury_indicators = ['luxury', 'premium', 'exclusive', 'designer', 'high-end']
        luxury_score = sum(1 for indicator in luxury_indicators if indicator in text_content)
        
        # Look for value indicators
        value_indicators = ['affordable', 'cheap', 'discount', 'sale', 'budget']
        value_score = sum(1 for indicator in value_indicators if indicator in text_content)
        
        if luxury_score > value_score:
            positioning = 'premium'
        elif value_score > luxury_score:
            positioning = 'value'
        else:
            positioning = 'mid-market'
        
        return {
            'positioning': positioning,
            'luxury_score': luxury_score,
            'value_score': value_score
        }
    
    def _detect_language(self, soup):
        """Detect primary language of the marketplace"""
        lang_attr = soup.find('html', {'lang': True})
        if lang_attr:
            return lang_attr.get('lang', 'en')[:2]
        
        # Fallback: analyze text content
        text_sample = soup.get_text()[:1000].lower()
        
        language_indicators = {
            'en': ['the', 'and', 'for', 'with', 'this', 'that'],
            'es': ['el', 'la', 'de', 'en', 'un', 'es'],
            'fr': ['le', 'de', 'et', 'à', 'un', 'il'],
            'de': ['der', 'die', 'und', 'in', 'den', 'von'],
            'it': ['il', 'di', 'e', 'la', 'in', 'da'],
            'pt': ['o', 'de', 'e', 'do', 'da', 'em']
        }
        
        language_scores = {}
        for lang, indicators in language_indicators.items():
            score = sum(1 for indicator in indicators if indicator in text_sample)
            language_scores[lang] = score
        
        return max(language_scores, key=language_scores.get) if language_scores else 'en'
    
    def _detect_country(self, soup):
        """Detect target country/region"""
        # Check for country indicators in URL
        domain = urlparse(self.marketplace_url).netloc.lower()
        
        country_domains = {
            '.uk': 'GB', '.co.uk': 'GB',
            '.de': 'DE', '.fr': 'FR', '.es': 'ES', '.it': 'IT',
            '.ca': 'CA', '.au': 'AU', '.jp': 'JP', '.br': 'BR',
            '.in': 'IN', '.cn': 'CN', '.mx': 'MX'
        }
        
        for domain_ext, country in country_domains.items():
            if domain_ext in domain:
                return country
        
        return 'US'  # Default
    
    def _detect_currency(self, soup):
        """Detect primary currency"""
        text_content = soup.get_text()
        
        currency_indicators = {
            'USD': ['$', 'usd', 'dollar'],
            'EUR': ['€', 'eur', 'euro'],
            'GBP': ['£', 'gbp', 'pound'],
            'JPY': ['¥', 'jpy', 'yen'],
            'INR': ['₹', 'inr', 'rupee']
        }
        
        for currency, indicators in currency_indicators.items():
            if any(indicator in text_content.lower() for indicator in indicators):
                return currency
        
        return 'USD'  # Default
    
    def generate_supplier_recommendations(self, marketplace_analysis, stores_df):
        """Generate supplier recommendations using real database"""
        print("🎯 Generating supplier recommendations from real database...")
        
        if stores_df is None or stores_df.empty:
            print("❌ No store data available")
            return []
        
        # Calculate compatibility scores for each store
        scored_stores = []
        
        for index, store in stores_df.iterrows():
            score = self._calculate_compatibility_score(store, marketplace_analysis)
            
            if score > 30:  # Only include stores with reasonable compatibility
                store_info = {
                    'store_name': store.get('URL', '').replace('https://', '').split('.')[0] if pd.notna(store.get('URL')) else f'Store_{index}',
                    'store_url': store.get('URL', '') if pd.notna(store.get('URL')) else '',
                    'categories': store.get('Categories', '') if pd.notna(store.get('Categories')) else '',
                    'description': store.get('Description', '')[:200] if pd.notna(store.get('Description')) else '',
                    'price_range': self._estimate_price_range(store),
                    'international_shipping': 'Yes' if 'International' in str(store.get('Ships To', '')) else 'Unknown',
                    'estimated_monthly_sales': store.get('Estimated Sales', '') if pd.notna(store.get('Estimated Sales')) else 'Unknown',
                    'compatibility_score': score,
                    'products_count': store.get('Products Count', '') if pd.notna(store.get('Products Count')) else 'Unknown'
                }
                scored_stores.append(store_info)
        
        # Sort by compatibility score
        scored_stores.sort(key=lambda x: x['compatibility_score'], reverse=True)
        
        # Return top suppliers
        recommended_suppliers = scored_stores[:self.max_suppliers]
        
        print(f"✅ Generated {len(recommended_suppliers)} supplier recommendations from real database")
        return recommended_suppliers
    
    def _calculate_compatibility_score(self, store, marketplace_analysis):
        """Calculate compatibility score between store and marketplace"""
        score = 0
        
        # Category matching
        store_categories = str(store.get('Categories', '')).lower()
        store_description = str(store.get('Description', '')).lower()
        marketplace_categories = marketplace_analysis['categories']
        
        # Check for category matches
        for category in marketplace_categories:
            if category in store_categories or category in store_description:
                score += 20
        
        # Price range compatibility
        marketplace_avg_price = marketplace_analysis['price_analysis']['average_price']
        if marketplace_avg_price > 0:
            # Estimate store price range from description
            estimated_sales = str(store.get('Estimated Sales', ''))
            if 'USD' in estimated_sales:
                # Extract numeric value from sales estimate
                sales_match = re.search(r'[\d,]+', estimated_sales)
                if sales_match:
                    try:
                        monthly_sales = float(sales_match.group().replace(',', ''))
                        if monthly_sales > 0:
                            # Rough estimate: monthly sales / 100 = average product price
                            estimated_avg_price = monthly_sales / 100
                            if abs(estimated_avg_price - marketplace_avg_price) < marketplace_avg_price * 0.5:
                                score += 25
                            elif abs(estimated_avg_price - marketplace_avg_price) < marketplace_avg_price:
                                score += 15
                    except:
                        pass
        
        # Brand positioning match
        brand_positioning = marketplace_analysis['brand_analysis']['positioning']
        if brand_positioning == 'premium' and any(word in store_description for word in ['premium', 'luxury', 'high-end', 'quality']):
            score += 15
        elif brand_positioning == 'value' and any(word in store_description for word in ['affordable', 'value', 'budget', 'cheap']):
            score += 15
        
        # International shipping bonus
        ships_to = str(store.get('Ships To', ''))
        if 'International' in ships_to or 'United States' in ships_to:
            score += 10
        
        # Product count bonus
        products_count = store.get('Products Count', 0)
        if pd.notna(products_count) and products_count > 0:
            if products_count > 100:
                score += 10
            elif products_count > 50:
                score += 5
        
        # Japanese origin bonus
        if any(word in store_description.lower() for word in ['japan', 'japanese', 'tokyo', 'osaka', 'kyoto']):
            score += 15
        
        return min(100, score)  # Cap at 100
    
    def _estimate_price_range(self, store):
        """Estimate price range from store data"""
        estimated_sales = str(store.get('Estimated Sales', ''))
        if 'USD' in estimated_sales:
            sales_match = re.search(r'[\d,]+', estimated_sales)
            if sales_match:
                try:
                    monthly_sales = float(sales_match.group().replace(',', ''))
                    if monthly_sales > 0:
                        # Rough estimate: monthly sales / 100 = average product price
                        avg_price = monthly_sales / 100
                        min_price = avg_price * 0.3
                        max_price = avg_price * 3
                        return f"${min_price:.0f}-${max_price:.0f}"
                except:
                    pass
        
        return "Unknown"
    
    def save_results(self, marketplace_analysis, suppliers):
        """Save analysis results to files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save CSV
        if suppliers:
            df = pd.DataFrame(suppliers)
            csv_filename = f'matching_results_{timestamp}.csv'
            df.to_csv(csv_filename, index=False)
            print(f"💾 CSV saved: {csv_filename}")
        
        # Save JSON summary
        summary = {
            'marketplace_analysis': marketplace_analysis,
            'supplier_recommendations': suppliers,
            'summary_stats': {
                'total_suppliers': len(suppliers),
                'avg_compatibility_score': sum(s['compatibility_score'] for s in suppliers) / len(suppliers) if suppliers else 0,
                'top_categories': marketplace_analysis['categories'][:5],
                'data_source': 'all_japan_stores_unlimited.csv'
            }
        }
        
        json_filename = f'matching_results_{timestamp}_summary.json'
        with open(json_filename, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"💾 JSON saved: {json_filename}")
        return csv_filename, json_filename

def main():
    if len(sys.argv) < 2:
        print("Usage: python github_actions_enhanced_analyzer.py <marketplace_url> [max_suppliers]")
        sys.exit(1)
    
    marketplace_url = sys.argv[1]
    max_suppliers = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    
    print(f"🚀 GitHub Actions Enhanced Marketplace Analyzer")
    print(f"   Marketplace: {marketplace_url}")
    print(f"   Max suppliers: {max_suppliers}")
    print("=" * 60)
    
    analyzer = GitHubActionsMarketplaceAnalyzer(marketplace_url, max_suppliers)
    
    # Load real database
    stores_df = analyzer.load_japanese_stores_database()
    if stores_df is None:
        print("❌ Could not load Japanese stores database")
        sys.exit(1)
    
    # Analyze marketplace
    marketplace_analysis = analyzer.analyze_marketplace()
    if not marketplace_analysis:
        print("❌ Failed to analyze marketplace")
        sys.exit(1)
    
    # Generate supplier recommendations using real data
    suppliers = analyzer.generate_supplier_recommendations(marketplace_analysis, stores_df)
    
    # Save results
    csv_file, json_file = analyzer.save_results(marketplace_analysis, suppliers)
    
    print("\n" + "=" * 60)
    print("✅ Analysis completed successfully!")
    print(f"📊 Marketplace: {marketplace_analysis['title']}")
    print(f"🏷️  Categories: {', '.join(marketplace_analysis['categories'][:3])}")
    print(f"💰 Avg Price: ${marketplace_analysis['price_analysis']['average_price']}")
    print(f"🎯 Suppliers: {len(suppliers)} recommendations from real database")
    print(f"📁 Files: {csv_file}, {json_file}")

if __name__ == "__main__":
    main()
