#!/usr/bin/env python3
import os

os.chdir('d:\\need for speed\\FILM PRODUCTION')

with open('templates/admin.html', 'r') as f:
    content = f.read()

new_card = '''        <article>
            <div class="card-head">
                <span class="card-icon">💌</span>
                <h2>Customer Conversations</h2>
            </div>
            <p>Manage and reply to customer conversations and inquiries.</p>
            <a class="button button-secondary" href="/admin/conversations">View Conversations</a>
        </article>
'''

# Insert before Team Schedule card
if '📅' in content and '💬' not in content:
    content = content.replace(
        '<span class="card-icon">💬</span>',
        ''
    )
    # Find the position to insert
    idx = content.find('<span class="card-icon">📅</span>')
    if idx > 0:
        # Find the start of the article tag before this position
        start = content.rfind('<article>', 0, idx)
        content = content[:start] + new_card + content[start:]

with open('templates/admin.html', 'w') as f:
    f.write(content)

print('Admin dashboard updated')
