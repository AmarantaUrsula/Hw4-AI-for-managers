# Problem 6 — tool lookup tests

Run 2026-10-24 11:54 against `data/campus_customs_new.db` with the live agent (gpt-6-luna via Portkey). For each reply, every `$` price and stock count was checked against the database.

## 1. How much is the Basic Hoodie Big Yale?

- **Expected:** price $68.00
- **Tools called (last turn):** `get_product_price(product='Basic Hoodie Big Yale')`
- **Reply:** The Basic Hoodie Big Yale is $68.00.
- **Cards:** basic-hoodie-big-yale
- **Numbers in reply:** prices [68.0], quantities — → ✅ all found in the database

## 2. Do you have the Davenport College Crewneck in a small?

- **Expected:** S sold out, other sizes offered
- **Tools called (last turn):** `get_stock(product='Davenport College Crewneck', size='small')`, `find_alternatives(product='davenport-college-crewneck', size='S', limit=4)`
- **Reply:** Size S is sold out in the Davenport College Crewneck. Similar crewneck styles available in S include the Jonathan Edwards College Crewneck (25 in stock), Baseball Left Chest Crewneck (15 in stock), and Yale Cousin Crewneck (25 in stock).
- **Cards:** davenport-college-crewneck, jonathan-edwards-college-crewneck, baseball-left-chest-crewneck, yale-cousin-crewneck
- **Numbers in reply:** prices —, quantities [25, 15, 25] → ✅ all found in the database

## 3. How many Basic Hoodie Big Yale are left in XL?

- **Expected:** XL: only 2 left
- **Tools called (last turn):** `get_stock(product='Basic Hoodie Big Yale', size='XL')`
- **Reply:** Only 2 left in XL for the Basic Hoodie Big Yale.
- **Cards:** basic-hoodie-big-yale
- **Numbers in reply:** prices —, quantities [2] → ✅ all found in the database

## 4. What sizes does the Fencing Left Chest Hoodie come in?

- **Expected:** XS, L, XXL sold out; S, M, XL available
- **Tools called (last turn):** `get_stock(product='Fencing Left Chest Hoodie')`
- **Reply:** The Fencing Left Chest Hoodie comes in XS, S, M, L, XL, and XXL. Right now, S and M are in stock, XL has only 2 left, and XS, L, and XXL are sold out.
- **Cards:** fencing-left-chest-hoodie
- **Numbers in reply:** prices —, quantities [2] → ✅ all found in the database

## 5. Tell me about the Boola Boola T-shirt.

- **Expected:** description from DB
- **Tools called (last turn):** `search_products(query='Boola Boola T-shirt', limit=6)`, `get_product_description(product='boola-boola-t-shirt')`, `get_product_price(product='boola-boola-t-shirt')`
- **Reply:** The Boola Boola T Shirt is a navy short-sleeve tee with a bold, distressed white-and-gray bubble-letter BOOLA BOOLA graphic across the chest. It’s $32.00.
- **Cards:** boola-boola-t-shirt
- **Numbers in reply:** prices [32.0], quantities — → ✅ all found in the database

## 6. I want the Yale Mom Crewneck in XXXL

- **Expected:** we stock XS–XXL
- **Tools called (last turn):** `search_products(query='Yale Mom', category_name='Crewneck', limit=5)`, `search_products(query='Yale Mom', limit=8)`, `get_stock(product='yale-mom-crewneck', size='XXXL')`, `get_product_description(product='yale-mom-crewneck')`
- **Reply:** The Yale Mom Crewneck isn’t available in XXXL; we carry sizes XS through XXL. XXL is the closest size, and it’s low in stock—only 2 left.
- **Cards:** yale-mom-crewneck
- **Numbers in reply:** prices —, quantities [2] → ✅ all found in the database

## 7. Is the Champion Reverse Weave Hoodie on sale? Can I get it for $50?

- **Expected:** exact price, no invented discount
- **Tools called (last turn):** `search_products(query='Champion Reverse Weave Hoodie', limit=5)`, `get_product_price(product='champion-reverse-weave-hoodie-1')`
- **Reply:** The Champion Reverse Weave Hoodie is listed at $68.00, so it isn’t available for $50 based on the current price. I can’t confirm whether it’s on sale beyond that listed price.
- **Cards:** champion-reverse-weave-hoodie-1
- **Numbers in reply:** prices [68.0, 50.0], quantities — → ✅ all found in the database

## 8. What hockey stuff do you have? → How much is the hoodie and is there a large?

- **Expected:** follow-up: re-looks up price + L stock
- **Tools called (last turn):** `get_product_price(product='yale-sports-hoodie-hockey')`, `get_stock(product='yale-sports-hoodie-hockey', size='L')`
- **Reply:** The Yale Sports Hockey Hoodie is $68.00, and size L is in stock.
- **Cards:** yale-sports-hoodie-hockey
- **Numbers in reply:** prices [68.0], quantities — → ✅ all found in the database

**Result: all replies used only database prices and quantities.**
