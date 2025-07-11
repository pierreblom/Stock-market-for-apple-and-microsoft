import glob
import os
import logging
from collections import defaultdict


def cleanup_duplicate_csv_files():
    """Remove duplicate CSV files to prevent storage waste"""
    try:
        csv_files = glob.glob('data_exports/*.csv')
        file_groups = defaultdict(list)
        
        # Group files by symbol and type
        for file_path in csv_files:
            filename = os.path.basename(file_path)
            parts = filename.split('_')
            if len(parts) >= 3:
                symbol = parts[0]
                period = parts[1] if parts[1] != 'default' else 'daily'
                key = f"{symbol}_{period}"
                file_groups[key].append((file_path, os.path.getmtime(file_path)))
        
        deleted_count = 0
        kept_count = 0
        
        # Keep only the newest file for each group
        for key, files in file_groups.items():
            if len(files) > 1:
                # Sort by modification time, keep the newest
                files.sort(key=lambda x: x[1], reverse=True)
                newest_file = files[0][0]
                
                # Delete older duplicates
                for file_path, _ in files[1:]:
                    try:
                        os.remove(file_path)
                        deleted_count += 1
                    except Exception as e:
                        logging.warning(f"Failed to delete {file_path}: {e}")
                
                kept_count += 1
            elif len(files) == 1:
                kept_count += 1
        
        logging.info(f"🧹 Cleanup complete: Deleted {deleted_count} duplicate files, kept {kept_count} unique files")
        return {'deleted': deleted_count, 'kept': kept_count}
        
    except Exception as e:
        logging.error(f"❌ Cleanup failed: {e}")
        return {'deleted': 0, 'kept': 0} 