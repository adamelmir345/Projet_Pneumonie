import os
import glob

# Paths to search
paths = [
    'medical_app/templates/medical_app/*.html',
    'finance/templates/finance/*.html'
]

files = []
for p in paths:
    files.extend(glob.glob(p))

target_str = '<div class="w-12 h-12 rounded-[1rem] bg-gradient-to-br from-primary to-primary-container flex items-center justify-center text-on-primary shadow-lg shadow-primary/20 font-headline-md">{{ user.username|make_list|first|upper }}</div>'
replacement_str = '''<div class="w-12 h-12 rounded-[1rem] bg-gradient-to-br from-primary to-primary-container flex items-center justify-center text-on-primary shadow-lg shadow-primary/20 font-headline-md overflow-hidden">
    {% if user.profile.photo_profil %}
        <img src="{{ user.profile.photo_profil.url }}" alt="Avatar" class="w-full h-full object-cover">
    {% else %}
        {{ user.username|make_list|first|upper }}
    {% endif %}
</div>'''

for file in files:
    with open(file, 'r') as f:
        content = f.read()
    
    if target_str in content:
        content = content.replace(target_str, replacement_str)
        with open(file, 'w') as f:
            f.write(content)
        print(f"Updated {file}")
