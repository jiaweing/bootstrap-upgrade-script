import os
import re
from pathlib import Path
import shutil

REPLACEMENTS = {
    # Float classes
    r'float-.*right\b': 'float-end',
    r'float-.*left\b': 'float-start',
    
    # Margin/Padding
    r'ml-([0-5x])\b': r'ms-\1',
    r'mr-([0-5x])\b': r'me-\1',
    r'pl-([0-5x])\b': r'ps-\1',
    r'pr-([0-5x])\b': r'pe-\1',
    
    # Forms
    r'form-group\b': 'mb-3',
    r'form-inline\b': 'd-flex',
    r'form-row\b': 'row g-3',
    r'custom-select\b': 'form-select',
    
    # File upload
    r'<div class="custom-file[^"]*"[^>]*>': '<div class="mb-3">',
    r'<input[^>]*type="file"[^>]*class="[^"]*custom-file-input[^"]*"[^>]*>': lambda m: m.group(0).replace('custom-file-input', 'form-control'),
    r'<label[^>]*class="[^"]*custom-file-label[^"]*"[^>]*>[^<]*</label>': '',
    r'<input[^>]*type="file"[^>]*(?!class="[^"]*form-control)[^>]*>': lambda m: m.group(0).replace('>', ' class="form-control">'),
    
    # Radio & Checkbox
    r'custom-control\b': 'form-check',
    r'custom-control-input\b': 'form-check-input',
    r'custom-control-label\b': 'form-check-label',
    r'custom-checkbox\b': 'form-check',
    r'custom-radio\b': 'form-check',
    r'custom-switch\b': 'form-switch',
    r'custom-control-inline\b': 'form-check-inline',
    
    # Range input
    r'custom-range\b': 'form-range',
    
    # Input groups
    r'input-group-prepend\b': 'input-group-text',
    r'input-group-append\b': 'input-group-text',
    
    # Buttons
    r'btn-block\b': 'w-100',
    
    # Text utilities
    r'text-left\b': 'text-start',
    r'text-right\b': 'text-end',
    r'text-monospace\b': 'font-monospace',
    r'text-hide\b': 'd-none',
    r'text-justify\b': '',  # Removed in BS5
    
    # Other utilities
    r'sr-only\b': 'visually-hidden',
    r'sr-only-focusable\b': 'visually-hidden-focusable',
    r'border-left\b': 'border-start',
    r'border-right\b': 'border-end',
    r'rounded-left\b': 'rounded-start',
    r'rounded-right\b': 'rounded-end',
    r'rounded-sm\b': 'rounded-1',
    r'rounded-lg\b': 'rounded-3',
    
    # Alert dialogs
    r'data-dismiss="alert"\b': 'data-bs-dismiss="alert"',
    r'alert-dismissible(?!\s+fade\s+show)\b': 'alert-dismissible fade show',
    r'<button[^>]*class="[^"]*close[^"]*"[^>]*>(?:\s*<span>\s*(?:&times;|×|✕|✖)\s*</span>\s*)</button>': '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>',
    r'<button[^>]*class="[^"]*close[^"]*"[^>]*>\s*(?:&times;|×|✕|✖)\s*</button>': '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>',
    r'<button[^>]*class="[^"]*close[^"]*"[^>]*>(?:\s|&nbsp;)*</button>': '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>',
    r'<div class="alert-body([^"]*)"[^>]*>([\s\S]*?)</div>': '\\2',
    r'class="alert([^"]*)"': 'class="alert\\1 d-flex align-items-center p-3"',
    
    # Navbar
    r'navbar-expand-([a-z]+)\b': r'navbar-expand-\1',  # Keep but check for proper breakpoint
    r'navbar-dark\s+bg-dark\b': 'navbar-dark bg-dark',  # Keep but check theme
    r'navbar-light\s+bg-light\b': 'navbar-light bg-light',  # Keep but check theme
    
    # Cards
    r'card-deck\b': 'row row-cols-1 row-cols-md-3 g-4',
    r'card-columns\b': 'row row-cols-1 row-cols-md-3 g-4',
    
    # Jumbotron
    r'jumbotron\b': 'bg-light p-5 rounded',
    r'jumbotron-fluid\b': 'bg-light px-5 py-5',
    
    # Responsive embeds
    r'embed-responsive\b': 'ratio',
    r'embed-responsive-16by9\b': 'ratio ratio-16x9',
    r'embed-responsive-21by9\b': 'ratio ratio-21x9',
    r'embed-responsive-4by3\b': 'ratio ratio-4x3',
    r'embed-responsive-1by1\b': 'ratio ratio-1x1',
    r'embed-responsive-item\b': 'ratio-item',
    
    # Tables
    r'table-responsive-([a-z]+)\b': r'table-responsive-\1',  # Keep but check breakpoint
    r'thead-light\b': 'table-light',
    r'thead-dark\b': 'table-dark',
    
    # Badges
    r'badge-pill\b': 'rounded-pill',
    
    # Size utilities
    r'size-([0-9]+)\b': r'size-\1',  # Check and update size utilities
    
    # Display utilities
    r'd-([a-z]+)-block\b': r'd-\1-block',  # Check responsive display utilities
    
    # Position utilities
    r'fixed-top\b': 'fixed-top',  # Keep but check implementation
    r'fixed-bottom\b': 'fixed-bottom',  # Keep but check implementation
    r'sticky-top\b': 'sticky-top',  # Keep but check implementation,
    
    # Tabs and Pills
    r'nav-tabs\s+nav-justified\b': 'nav-tabs nav-fill',
    r'nav-pills\s+nav-justified\b': 'nav-pills nav-fill',
    r'\sdata-toggle\s*=\s*["\']tab["\']': ' data-bs-toggle="tab"',
    r'\sdata-toggle\s*=\s*["\']pill["\']': ' data-bs-toggle="pill"',
    r'\sdata-toggle\s*=\s*["\']list["\']': ' data-bs-toggle="list"',
    r'role="tab"\b': 'role="tab"',
    r'aria-controls=["\']([^"\']+)["\']': r'aria-controls="\1"',
    r'aria-selected=["\']([^"\']+)["\']': r'aria-selected="\1"',
    r'tab-content\b(?!\s+fade\s+show)': 'tab-content fade show',
    r'tab-pane\b(?!\s+fade\s+show)': 'tab-pane fade show',
    
    # Dropdowns
    r'<a[^>]*data-bs-toggle="dropdown"[^>]*>': lambda m: m.group(0).replace('>', ' role="button">') if 'role=' not in m.group(0) else m.group(0),
    r'\sdata-toggle=["\']dropdown["\']': ' data-bs-toggle="dropdown"',
    r'\sdata-toggle\s*=\s*["\']dropdown["\']': ' data-bs-toggle="dropdown"',
    r'data-reference=["\']parent["\']': 'data-bs-reference="parent"',
    r'data-offset=["\']([^"\']+)["\']': r'data-bs-offset="\1"',
    r'data-flip=["\']([^"\']+)["\']': r'data-bs-flip="\1"',
    r'data-boundary=["\']([^"\']+)["\']': r'data-bs-boundary="\1"',
    r'data-display=["\']([^"\']+)["\']': r'data-bs-display="\1"',
    r'dropdown-menu-(left|right)\b': 'dropdown-menu-end',
    r'dropleft\b': 'dropstart',
    r'dropright\b': 'dropend',
    r'dropdown-menu-right\b': 'dropdown-menu-end',
    r'dropdown-menu-left\b': 'dropdown-menu-start',
    r'dropdown-toggle-split\b': 'dropdown-toggle-split',  # Keep but verify
    
    # Popper positioning
    r'data-placement="([^"]+)"\b': r'data-bs-placement="\1"',

    # Tab fixes
    r'<a[^>]*class="[^"]*nav-link[^"]*"[^>]*data-bs-toggle="tab"[^>]*href="([^"]*)"([^>]*)>': 
        lambda m: m.group(0).replace(f'href="{m.group(1)}"', f'href="{m.group(1)}" data-bs-target="{m.group(1)}"'),
    
    # Tab pane fixes
    r'<div[^>]*class="[^"]*tab-pane[^"]*"[^>]*>(?![^<]*\bfade\b)': 
        lambda m: m.group(0).replace('tab-pane', 'tab-pane fade'),
    r'<div[^>]*class="[^"]*tab-pane\s+active[^"]*"[^>]*>(?![^<]*\bshow\b)':
        lambda m: m.group(0).replace('active', 'active show'),

    # Modal fixes
    r'\sdata-toggle="modal"': ' data-bs-toggle="modal"',
    r'\sdata-target="([^"]+)"': r' data-bs-target="\1"',
    r'\sdata-dismiss="modal"': ' data-bs-dismiss="modal"',
    r'<button[^>]*class="[^"]*close[^"]*"[^>]*>\s*(?:<span[^>]*>[^<]*</span>\s*)?</button>':
        '<button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>',
    r'<div class="modal fade"([^>]*)>(?![^<]*\sdata-bs-backdrop=)':
        '<div class="modal fade" data-bs-backdrop="true"\\1>',
    r'<div class="modal-dialog([^"]*)"([^>]*)>(?![^<]*\sdata-bs-keyboard=)':
        '<div class="modal-dialog\\1"\\2 data-bs-keyboard="true">',
    r'modal-dialog(?!\s+modal-dialog-scrollable)(\s+modal-dialog-centered)': 
        'modal-dialog modal-dialog-scrollable\\1',
}

def upgrade_bootstrap(directory):
    file_types = ['*.html', '*.cshtml', '*.css', '*.js', '*.jsx', '*.ts', '*.tsx', '*.vue']
    changes_made = 0
    files_modified = 0
    files_processed = 0
    
    print("\nScanning for Bootstrap 4 classes...")
    
    for pattern in file_types:
        for path in Path(directory).rglob(pattern):
            files_processed += 1
            file_changes = upgrade_file(path)
            if file_changes > 0:
                changes_made += file_changes
                files_modified += 1
    
    print(f"\nUpgrade Summary:")
    print(f"Files processed: {files_processed}")
    print(f"Files modified: {files_modified}")
    print(f"Total changes made: {changes_made}")
    print("\nNOTE: Backup files have been created with '.bak' extension")
    print("Please verify the changes before removing the backups.")

def upgrade_file(filepath):
    changes = 0
    try:
        print(f"Processing {filepath}")
        
        # Create backup
        backup_path = str(filepath) + '.bak'
        shutil.copy2(filepath, backup_path)
        
        # Read content
        with open(filepath, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Make replacements
        modified = False
        new_content = content
        
        for old, new in REPLACEMENTS.items():
            matches = len(re.findall(old, content))
            if matches > 0:
                new_content = re.sub(old, new, new_content)
                modified = True
                changes += matches
                print(f"  • {old} → {new} ({matches} occurrences)")
        
        # Write changes if modified
        if modified:
            with open(filepath, 'w', encoding='utf-8') as file:
                file.write(new_content)
            print(f"✓ Updated {filepath} ({changes} changes)")
        
        return changes
    
    except Exception as e:
        print(f"Error processing {filepath}: {str(e)}")
        return 0

if __name__ == "__main__":
    print("Bootstrap 4 to 5 Upgrade Tool")
    print("----------------------------")
    directory = input("Enter project directory path: ")
    
    if not os.path.isdir(directory):
        print("Error: Invalid directory path")
    else:
        upgrade_bootstrap(directory)
        print("\nBootstrap upgrade complete!")
