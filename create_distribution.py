import os
import shutil
import zipfile

def create_distribution():
    # Clean up old distribution files
    if os.path.exists('dist.zip'):
        os.remove('dist.zip')
    
    # Create ZIP file
    with zipfile.ZipFile('Dave.zip', 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add the executable
        zipf.write(os.path.join('dist', 'Dave.exe'), 'Dave.exe')
        
        # Add README
        zipf.write('README.md')
        
        print("Distribution package created: Dave.zip")

if __name__ == '__main__':
    create_distribution()
