import io
import xml.etree.ElementTree as ET
import pandas as pd
import requests
import time

# CRITICAL: Identify yourself clearly to the SEC or your script will get blocked immediately.
SEC_HEADERS = {
    "User-Agent": "Your Name your.email@example.com",
    "Accept-Encoding": "gzip, deflate"
}

def get_daily_form_4_index(date_str):
    """
    Step 1.1: Downloads the master SEC index file for a specific day and filters for Form 4s.
    date_str format: 'YYYYMMDD' (e.g., '20260310')
    """
    year = date_str[0:4]
    month = date_str[4:6]
    
    # Calculate Quarter (QTR1, QTR2, QTR3, QTR4)
    qtr = ((int(month) - 1) // 3) + 1
    
    url = f"https://www.sec.gov/Archives/edgar/daily-index/{year}/QTR{qtr}/master.{date_str}.idx"
    print(f"📡 Fetching daily index from: {url}")
    
    response = requests.get(url, headers=SEC_HEADERS)
    if response.status_code != 200:
        print(f"❌ Failed to fetch index for {date_str}. Status: {response.status_code}")
        return None
    
    # Locate where the actual data table starts (after the dashed lines)
    lines = response.text.split('\n')
    data_start_idx = 0
    for i, line in enumerate(lines):
        if line.startswith('-----------'):
            data_start_idx = i + 1
            break
            
    clean_data = "\n".join(lines[data_start_idx:])
    
    columns = ['CIK', 'Company Name', 'Form Type', 'Date Filed', 'File Name']
    df = pd.read_csv(io.StringIO(clean_data), sep='|', names=columns, index_col=False)
    
    # Keep only Form 4 filings
    form_4_df = df[df['Form Type'] == '4'].copy()
    return form_4_df


def convert_to_xml_url(file_name_path):
    """
    Step 1.2: Converts a standard index file path into a direct XML URL.
    Example Input: 'edgar/data/1326801/0001326801-26-000015.txt'
    Example Output: 'https://www.sec.gov/Archives/edgar/data/1326801/000132680126000015/form4.xml'
    """
    # Remove .txt extension
    base_path = file_name_path.replace('.txt', '')
    # Remove dashes from the accession number segment
    parts = base_path.split('/')
    parts[-1] = parts[-1].replace('-', '')
    
    reconstructed_dir = "/".join(parts)
    return f"https://www.sec.gov/Archives/{reconstructed_dir}/form4.xml"


def parse_form_4_xml(xml_url):
    """
    Step 1.3: Downloads a single Form 4 XML and extracts insider trade metrics.
    """
    try:
        response = requests.get(xml_url, headers=SEC_HEADERS)
        if response.status_code != 200:
            return [] # Skip if XML doesn't exist at this direct path (some old historical filings vary)
        
        root = ET.fromstring(response.content)
        
        ticker = root.findtext('.//issuerTradingSymbol')
        owner_name = root.findtext('.//rptOwnerName')
        is_director = root.findtext('.//isDirector') in ['true', '1']
        is_officer = root.findtext('.//isOfficer') in ['true', '1']
        officer_title = root.findtext('.//officerTitle')
        
        parsed_trades = []
        
        # Look for non-derivative transactions (Direct stock buys/sales)
        for tx in root.findall('.//nonDerivativeTransaction'):
            tx_code = tx.findtext('.//transactionCode')
            
            # We strictly focus on Open Market Purchases (P) and Open Market Sales (S)
            if tx_code in ['P', 'S']:
                shares = tx.findtext('.//transactionShares/value')
                price = tx.findtext('.//transactionPricePerShare/value')
                date = tx.findtext('.//transactionDate/value')
                
                shares_f = float(shares) if shares else 0.0
                price_f = float(price) if price else 0.0
                
                if shares_f > 0 and price_f > 0:
                    parsed_trades.append({
                        "ticker": ticker,
                        "insider_name": owner_name,
                        "title": officer_title if is_officer else ("Director" if is_director else "10% Owner"),
                        "trade_date": date,
                        "transaction_type": tx_code, # 'P' or 'S'
                        "shares": shares_f,
                        "price": price_f,
                        "total_value": shares_f * price_f
                    })
        return parsed_trades
    except Exception as e:
        # Silently absorb occasional malformed XML errors during testing
        return []

# --- Run a Test Sample for Phase 1 & 2 Together ---
if __name__ == "__main__":
    # Import the database functions we just wrote
    from phase2_database import init_database, save_trades_to_db
    
    # Initialize the database file
    init_database()
    
    target_date = "20260310"
    index_df = get_daily_form_4_index(target_date)
    
    if index_df is not None and not index_df.empty:
        print(f"✅ Found {len(index_df)} Form 4 entries in the index.")
        
        all_extracted_trades = []
        
        # Let's up the sample size slightly to 30 to get a good batch of data saved!
        sample_subset = index_df.head(30)
        print("Parsing a sample of 30 filings...")
        
        for idx, row in sample_subset.iterrows():
            xml_endpoint = convert_to_xml_url(row['File Name'])
            trades = parse_form_4_xml(xml_endpoint)
            all_extracted_trades.extend(trades)
            time.sleep(0.1) # Respect the SEC
            
        # SAVE TO DATABASE
        saved_rows = save_trades_to_db(all_extracted_trades)
        print(f"💾 Successfully saved {saved_rows} new transactions to your local database file!")