with open('templates/item_detail.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

# Fix the curly braces
text = text.replace('const price = {{ item.rental_price }', 'const price = {{ item.rental_price }};')

# Fix the broken RS symbol due to encoding
text = text.replace(',1{{ item.rental_price }}', '₹{{ item.rental_price }}')
text = text.replace(',1<span id="total_price">', '₹<span id="total_price">')

# Also fix the general {{ item.rental_price }}
text = text.replace('const price = {{ item.rental_price }};;', 'const price = {{ item.rental_price }};')
text = text.replace('const price = {{ item.rental_price }\n                };', 'const price = {{ item.rental_price }};')

# Some more explicit fixes from the Get-Content log
text = text.replace('const price = {{ item.rental_price }\n                };\n                document.getElementById(\'total_price\').innerText = (days * price).toFixed(2);\n                }', 'const price = {{ item.rental_price }};\n                    document.getElementById(\'total_price\').innerText = (days * price).toFixed(2);\n                }')

with open('templates/item_detail.html', 'w', encoding='utf-8') as f:
    f.write(text)
