"""
Google Sheets Data Handler
Fetches client data from Google Sheets with caching
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials
import yaml
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import sys


class GoogleSheetsHandler:
    def __init__(self, config_path: str = "config/config.yaml"):
        """Initialize Google Sheets handler with configuration"""
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        with open("config/sheet_config.yaml", 'r') as f:
            self.sheet_config = yaml.safe_load(f)
        
        self.client = None
        self.sheet = None
        self.cache = None
        self.cache_timestamp = None
        self._connect()
    
    def _connect(self):
        """Establish connection to Google Sheets"""
        try:
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive'
            ]
            
            creds_path = self.config['google_sheets']['credentials_path']
            credentials = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
            self.client = gspread.authorize(credentials)
            
            sheet_id = self.config['google_sheets']['sheet_id']
            self.sheet = self.client.open_by_key(sheet_id)
            
        except FileNotFoundError:
            print("❌ Error: credentials.json not found in config/ directory")
            print("Please place your Google Sheets API credentials in config/credentials.json")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Error connecting to Google Sheets: {str(e)}")
            sys.exit(1)
    
    def _is_cache_valid(self) -> bool:
        """Check if cache is still valid"""
        if self.cache is None or self.cache_timestamp is None:
            return False
        
        cache_duration = self.config['google_sheets']['cache_duration_seconds']
        return datetime.now() - self.cache_timestamp < timedelta(seconds=cache_duration)
    
    def fetch_all_data(self, force_refresh: bool = False) -> List[List]:
        """Fetch all data from sheet with caching"""
        if not force_refresh and self._is_cache_valid():
            return self.cache
        
        try:
            sheet_name = self.config['google_sheets']['sheet_name']
            worksheet = self.sheet.worksheet(sheet_name)
            
            # Get all values (skip header row)
            all_data = worksheet.get_all_values()[1:]  # Skip header
            
            self.cache = all_data
            self.cache_timestamp = datetime.now()
            
            return all_data
            
        except Exception as e:
            print(f"❌ Error fetching data from Google Sheets: {str(e)}")
            if self.cache:
                print("⚠️  Using cached data instead...")
                return self.cache
            sys.exit(1)
    
    def get_clients_by_pop(self, pop_name: str) -> List[Dict[str, str]]:
        """Get all clients for a specific POP"""
        all_data = self.fetch_all_data()
        
        col_indices = self.sheet_config['indices']
        client_name_idx = col_indices['client_name']
        connected_pop_idx = col_indices['connected_pop']
        base_ap_ip_idx = col_indices['base_ap_ip']
        
        clients = []
        for row in all_data:
            # Safety check for row length
            if len(row) <= max(client_name_idx, connected_pop_idx, base_ap_ip_idx):
                continue
            
            # Filter by POP name (case-insensitive)
            if row[connected_pop_idx].strip().lower() == pop_name.strip().lower():
                client_name = row[client_name_idx].strip()
                ip_address = row[base_ap_ip_idx].strip()
                
                # Skip if no IP or client name
                if not ip_address or not client_name:
                    continue
                
                clients.append({
                    'client_name': client_name,
                    'ip_address': ip_address,
                    'pop_name': row[connected_pop_idx].strip()
                })
        
        return clients
    
    def get_all_pops(self) -> List[str]:
        """Get list of all unique POP names"""
        all_data = self.fetch_all_data()
        
        col_idx = self.sheet_config['indices']['connected_pop']
        
        pops = set()
        for row in all_data:
            if len(row) > col_idx and row[col_idx].strip():
                pops.add(row[col_idx].strip())
        
        return sorted(list(pops))
